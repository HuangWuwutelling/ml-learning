"""Load Card & Krueger (1994) fast-food minimum wage panel summary.

Source: Card, D. & Krueger, A.B. (1994), "Minimum Wages and Employment:
A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania",
American Economic Review 84(4): 772-793. Table 2 (Mean FTE employment).

Original microdata (410 stores x 2 waves = 820 rows) is hosted at
David Card's Berkeley homepage:
    https://davidcard.berkeley.edu/data_sets.html

This loader returns the aggregated 2x2 means published in Table 2 of the
paper, sufficient for the 2x2 difference-in-differences demonstration in
causal/02. To access microdata, download the njmin.zip file from Card's
homepage and parse public.dat directly.

Public functions:
    load_card_krueger_aggregated() -> pd.DataFrame
        4-row long form: state, period, mean_fte, n_stores
    load_card_krueger_microdata(data_dir) -> pd.DataFrame
        Full 410 stores x 2 waves = 820 rows panel from public.dat
    compute_did_2x2(df) -> dict
        nj_pre, nj_post, pa_pre, pa_post, nj_diff, pa_diff, did
"""
import os
import pandas as pd


def load_card_krueger_aggregated():
    """Card & Krueger (1994) Table 2 summary for NJ vs PA fast food.

    Returns a DataFrame in long form with columns:
        state, period, mean_fte, n_stores
    where period is 'pre' or 'post'.
    """
    rows = [
        # state, period, mean_fte, n_stores
        # Source: Card & Krueger 1994 AER 84(4) Table 2 'All Stores' column
        ('NJ', 'pre',  20.44, 331),
        ('NJ', 'post', 21.03, 331),
        ('PA', 'pre',  23.33,  79),
        ('PA', 'post', 21.17,  79),
    ]
    return pd.DataFrame(rows, columns=['state', 'period', 'mean_fte', 'n_stores'])


def load_card_krueger_microdata(data_dir):
    """Load microdata from Card's njmin dataset (if locally available).

    Parameters
    ----------
    data_dir : str
        Path to directory containing 'public.dat' (the Card-Krueger
        1994 panel of 410 fast-food restaurants).

    Returns
    -------
    pd.DataFrame
        Long-form panel: one row per (store, wave).
    """
    # public.dat is a space-delimited file without headers
    # 410 stores x 2 waves, plus a few identifier columns
    path = os.path.join(data_dir, 'public.dat')
    cols = [
        'sheet', 'nj', 'wave', 'chain', 'store_id',
        'empft', 'emppt', 'empfte', 'nmgrs', 'wage_st',
        'inctime', 'firstinc', 'bonus', 'pctaff', 'meals',
        'open', 'hrsopen', 'psoda', 'pfries', 'pentree',
        'nregs', 'nregs11', 'type2', 'status2', 'date2',
        'mood', 'mood3',
    ]
    df = pd.read_csv(path, sep=r'\s+', header=None, names=cols,
                     na_values=['.', ''], engine='python')
    df['state'] = df['nj'].map({1: 'NJ', 0: 'PA'})
    df['period'] = df['wave'].map({1: 'pre', 2: 'post'})
    return df


def compute_did_2x2(df):
    """Compute the 2x2 difference-in-differences estimate.

    Parameters
    ----------
    df : pd.DataFrame
        Must have columns: state ('NJ'/'PA'), period ('pre'/'post'),
        and one column to average (default: 'mean_fte').

    Returns
    -------
    dict
        nj_pre, nj_post, pa_pre, pa_post,
        nj_diff, pa_diff, did
    """
    col = 'mean_fte' if 'mean_fte' in df.columns else 'empfte'
    nj_pre  = df[(df['state'] == 'NJ') & (df['period'] == 'pre')][col].mean()
    nj_post = df[(df['state'] == 'NJ') & (df['period'] == 'post')][col].mean()
    pa_pre  = df[(df['state'] == 'PA') & (df['period'] == 'pre')][col].mean()
    pa_post = df[(df['state'] == 'PA') & (df['period'] == 'post')][col].mean()
    nj_diff = nj_post - nj_pre
    pa_diff = pa_post - pa_pre
    did = nj_diff - pa_diff
    return {
        'nj_pre': nj_pre, 'nj_post': nj_post,
        'pa_pre': pa_pre, 'pa_post': pa_post,
        'nj_diff': nj_diff, 'pa_diff': pa_diff,
        'did': did,
    }


if __name__ == '__main__':
    df = load_card_krueger_aggregated()
    print('Loaded Card & Krueger 1994 Table 2 summary:')
    print(df.to_string(index=False))
    print()
    print('DID estimate (NJ vs PA, FTE):')
    res = compute_did_2x2(df)
    for k, v in res.items():
        print(f'  {k}: {v:+.2f}')