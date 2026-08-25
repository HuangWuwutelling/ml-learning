"""Propensity Score Matching (PSM) — Rosenbaum & Rubin 1983.

观测性研究里用来剥离 confounder 的经典方法。三步：
1. 用 logistic 回归估计每个样本的倾向得分 P(T=1|X)
2. 按倾向得分给处理组找 k 个最接近的控制组（带卡尺过滤）
3. 配对后比较两组的 outcome，差值就是 ATT

倾向得分用 sklearn LogisticRegression（max_iter=1000）保证数值稳定；
匹配算法（SMD + ATT）用 numpy 手写。倾向得分模型的选择对最终数字
有显著影响（手写梯度下降在小样本下精度不足），本仓库默认采用 sklearn。
"""
import numpy as np
from sklearn.linear_model import LogisticRegression


class PropensityScoreMatching:
    """Propensity Score Matching estimator.

    Parameters
    ----------
    k : int, default=4
        每个处理组样本匹配的控制组样本数（Rosenbaum & Rubin 1983 原文 1:1，
        k>1 的多对照配对经 Stuart 2010 验证）。
    caliper_factor : float, default=0.2
        卡尺倍数：caliper = caliper_factor * std(propensity)。
        倾向得分差距超过卡尺的配对直接丢弃。
    max_iter : int, default=1000
        内部 sklearn LogisticRegression 的最大迭代次数。

    Attributes (after fit)
    ----------------------
    propensity_ : ndarray of shape (n,)
        每个样本的倾向得分 P(T=1|X)。
    logreg_ : sklearn LogisticRegression
        拟合的 logistic 模型。
    caliper_ : float
        配对时使用的卡尺阈值。

    Examples
    --------
    >>> psm = PropensityScoreMatching(k=4, caliper_factor=0.2)
    >>> psm.fit(X_confounders, T_treatment)
    >>> matched_pairs = psm.match(T_treatment)  # [(t_idx, c_idx), ...]
    >>> att = PropensityScoreMatching.estimate_att(Y_outcome, T_treatment, matched_pairs)
    >>> smd_after = PropensityScoreMatching.smd(X_confounders, T_treatment, matched_pairs)
    """

    def __init__(self, k=4, caliper_factor=0.2, max_iter=1000):
        self.k = k
        self.caliper_factor = caliper_factor
        self.max_iter = max_iter

    def fit(self, X, T):
        """估计倾向得分 + 计算卡尺。

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            confounder 矩阵。
        T : ndarray of shape (n_samples,)
            处理组指示向量（0/1）。

        Returns
        -------
        self
        """
        X = np.asarray(X, dtype=float)
        T = np.asarray(T)
        self.logreg_ = LogisticRegression(max_iter=self.max_iter)
        self.logreg_.fit(X, T)
        self.propensity_ = self.logreg_.predict_proba(X)[:, 1]
        self.caliper_ = self.caliper_factor * np.std(self.propensity_)
        return self

    def match(self, T, user_ids=None):
        """按倾向得分给处理组配 k 个控制组（向量化 k-NN + 卡尺过滤）。

        Parameters
        ----------
        T : ndarray of shape (n_samples,)
            处理组指示向量（0/1）。
        user_ids : array-like of shape (n_samples,), optional
            每个样本的 user-level 标识（如 user_id）。若提供，配对结果返回
            user_id；否则返回样本行号索引。

        Returns
        -------
        matched_pairs : list of (t_key, c_key)
            配对 key，处理组在前、控制组在后。卡尺外的处理组样本直接舍弃。
        """
        T = np.asarray(T)
        ps = self.propensity_
        t_idx_all = np.where(T == 1)[0]
        c_idx_all = np.where(T == 0)[0]
        ps_t = ps[t_idx_all]
        ps_c = ps[c_idx_all]
        caliper = self.caliper_
        keys_t = user_ids[t_idx_all] if user_ids is not None else t_idx_all
        keys_c = user_ids[c_idx_all] if user_ids is not None else c_idx_all

        matched_pairs = []
        for i, ps_i in enumerate(ps_t):
            lo, hi = ps_i - caliper, ps_i + caliper
            candidates = np.where((ps_c >= lo) & (ps_c <= hi))[0]
            if len(candidates) < self.k:
                continue  # 卡尺内候选不足，舍弃该处理组样本
            dists = np.abs(ps_c[candidates] - ps_i)
            top_k = candidates[np.argsort(dists)[:self.k]]
            for c_idx in top_k:
                matched_pairs.append((int(keys_t[i]), int(keys_c[c_idx])))
        return matched_pairs

    @staticmethod
    def smd(X, T, matched_pairs=None):
        """计算每个 confounder 的标准化均值差（Standardized Mean Difference）。

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
        T : ndarray of shape (n_samples,)
        matched_pairs : list of (t_idx, c_idx), optional
            若提供，配对后两组的 SMD；否则全部样本的 SMD。

        Returns
        -------
        smd : dict[int -> float]
            每个 confounder 列索引到 SMD 值的映射。
        """
        X = np.asarray(X, dtype=float)
        T = np.asarray(T)
        if matched_pairs is None:
            t_mask = T == 1
            c_mask = T == 0
            Xt, Xc = X[t_mask], X[c_mask]
        else:
            t_idx = [t for t, c in matched_pairs]
            c_idx = [c for t, c in matched_pairs]
            Xt, Xc = X[t_idx], X[c_idx]
        smd = {}
        for j in range(X.shape[1]):
            t_mean, c_mean = Xt[:, j].mean(), Xc[:, j].mean()
            pooled = np.sqrt((Xt[:, j].var() + Xc[:, j].var()) / 2)
            smd[j] = abs(t_mean - c_mean) / pooled if pooled > 0 else 0.0
        return smd

    @staticmethod
    def estimate_att(Y, T, matched_pairs):
        """计算配对后的 ATT（处理组平均处理效应）。

        Parameters
        ----------
        Y : ndarray of shape (n_samples,)
            结果变量（如评分、GMV）。
        T : ndarray of shape (n_samples,)
            处理组指示向量。
        matched_pairs : list of (t_idx, c_idx)
            配对索引。

        Returns
        -------
        att : float
            处理组均值 - 控制组均值（配对后）。
        """
        t_idx = [t for t, c in matched_pairs]
        c_idx = [c for t, c in matched_pairs]
        att = Y[t_idx].mean() - Y[c_idx].mean()
        return float(att)