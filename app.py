import io
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from openai import OpenAI
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd


st.set_page_config(
    page_title="StatPharm Insight",
    page_icon="🔬",
    layout="wide",
)


APP_TITLE = "StatPharm Insight"
APP_SUBTITLE = "Dashboard otomatis untuk analisis data penelitian: deskriptif, uji asumsi, uji beda, post hoc, visualisasi, dan narasi hasil."


@st.cache_data
def load_example_data():
    return pd.read_csv("data/contoh_data_penelitian.csv")


def clean_numeric(series: pd.Series) -> pd.Series:
    """Convert a column to numeric safely."""
    return pd.to_numeric(series, errors="coerce")


def format_p(p_value):
    if pd.isna(p_value):
        return "-"
    if p_value < 0.001:
        return "<0,001"
    return f"{p_value:.3f}".replace(".", ",")


def significance_text(p_value, alpha=0.05):
    if pd.isna(p_value):
        return "tidak dapat disimpulkan"
    return "signifikan" if p_value < alpha else "tidak signifikan"


def descriptive_table(df, group_col, value_col):
    data = df[[group_col, value_col]].dropna().copy()
    grouped = data.groupby(group_col)[value_col]
    desc = grouped.agg([
        ("n", "count"),
        ("mean", "mean"),
        ("sd", "std"),
        ("median", "median"),
        ("min", "min"),
        ("max", "max"),
    ]).reset_index()
    desc["mean ± sd"] = desc.apply(
        lambda r: f"{r['mean']:.3f} ± {r['sd']:.3f}" if not pd.isna(r["sd"]) else f"{r['mean']:.3f} ± -",
        axis=1,
    )
    return desc


def shapiro_by_group(df, group_col, value_col):
    rows = []
    for group, values in df.groupby(group_col)[value_col]:
        vals = values.dropna().astype(float)
        if len(vals) >= 3:
            stat, p = stats.shapiro(vals)
            conclusion = "normal" if p >= 0.05 else "tidak normal"
        else:
            stat, p, conclusion = np.nan, np.nan, "data < 3, tidak diuji"
        rows.append({
            "kelompok": group,
            "n": len(vals),
            "statistik": stat,
            "p-value": p,
            "kesimpulan": conclusion,
        })
    return pd.DataFrame(rows)


def levene_test(df, group_col, value_col):
    groups = [g.dropna().astype(float).values for _, g in df.groupby(group_col)[value_col]]
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) < 2:
        return np.nan, np.nan, "kelompok kurang untuk uji homogenitas"
    stat, p = stats.levene(*groups, center="median")
    conclusion = "homogen" if p >= 0.05 else "tidak homogen"
    return stat, p, conclusion


def one_way_anova(df, group_col, value_col):
    groups = [g.dropna().astype(float).values for _, g in df.groupby(group_col)[value_col]]
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) < 2:
        return np.nan, np.nan
    stat, p = stats.f_oneway(*groups)
    return stat, p


def kruskal_test(df, group_col, value_col):
    groups = [g.dropna().astype(float).values for _, g in df.groupby(group_col)[value_col]]
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) < 2:
        return np.nan, np.nan
    stat, p = stats.kruskal(*groups)
    return stat, p


def tukey_posthoc(df, group_col, value_col):
    data = df[[group_col, value_col]].dropna().copy()
    if data[group_col].nunique() < 2:
        return pd.DataFrame()
    result = pairwise_tukeyhsd(endog=data[value_col], groups=data[group_col], alpha=0.05)
    table = pd.DataFrame(data=result._results_table.data[1:], columns=result._results_table.data[0])
    return table


def mannwhitney_pairwise(df, group_col, value_col):
    """Simple pairwise Mann-Whitney with Bonferroni correction for nonparametric follow-up."""
    data = df[[group_col, value_col]].dropna().copy()
    groups = sorted(data[group_col].unique())
    comparisons = []
    m = len(groups) * (len(groups) - 1) / 2
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            g1, g2 = groups[i], groups[j]
            v1 = data.loc[data[group_col] == g1, value_col].astype(float)
            v2 = data.loc[data[group_col] == g2, value_col].astype(float)
            if len(v1) < 2 or len(v2) < 2:
                continue
            stat, p = stats.mannwhitneyu(v1, v2, alternative="two-sided")
            p_adj = min(p * m, 1.0)
            comparisons.append({
                "kelompok_1": g1,
                "kelompok_2": g2,
                "U": stat,
                "p-value": p,
                "p-adj Bonferroni": p_adj,
                "kesimpulan": "berbeda signifikan" if p_adj < 0.05 else "tidak berbeda signifikan",
            })
    return pd.DataFrame(comparisons)


def make_boxplot(df, group_col, value_col):
    data = df[[group_col, value_col]].dropna().copy()
    labels = list(data[group_col].dropna().unique())
    values = [data.loc[data[group_col] == label, value_col].astype(float).values for label in labels]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.boxplot(values, tick_labels=labels, showmeans=True)
    ax.set_title(f"Distribusi {value_col} berdasarkan {group_col}")
    ax.set_xlabel(group_col)
    ax.set_ylabel(value_col)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def make_barplot(desc, group_col, value_col):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(desc[group_col]))
    means = desc["mean"].values
    sds = desc["sd"].fillna(0).values
    ax.bar(x, means, yerr=sds, capsize=5)
    ax.set_xticks(x)
    ax.set_xticklabels(desc[group_col].astype(str).values)
    ax.set_title(f"Rata-rata {value_col} per {group_col}")
    ax.set_xlabel(group_col)
    ax.set_ylabel(f"Mean ± SD {value_col}")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def generate_narrative(group_col, value_col, desc, shapiro_df, levene_result, main_test_name, main_stat, main_p):
    best_row = desc.loc[desc["mean"].idxmax()]
    normal_all = (shapiro_df["p-value"].dropna() >= 0.05).all() if not shapiro_df["p-value"].dropna().empty else False
    levene_stat, levene_p, levene_conclusion = levene_result
    normal_sentence = "seluruh kelompok berdistribusi normal" if normal_all else "tidak seluruh kelompok berdistribusi normal"

    text = (
        f"Data parameter {value_col} dianalisis berdasarkan kelompok {group_col}. "
        f"Hasil deskriptif menunjukkan nilai rata-rata tertinggi terdapat pada kelompok {best_row[group_col]} "
        f"dengan nilai {best_row['mean']:.3f} ± {best_row['sd']:.3f}. "
        f"Uji Shapiro-Wilk menunjukkan bahwa {normal_sentence}. "
        f"Uji Levene menunjukkan data {levene_conclusion} dengan p-value {format_p(levene_p)}. "
        f"Berdasarkan hasil tersebut, analisis dilanjutkan menggunakan {main_test_name}. "
        f"Hasil {main_test_name} menunjukkan p-value {format_p(main_p)}, sehingga perbedaan antar kelompok "
        f"dinyatakan {significance_text(main_p)} pada taraf kepercayaan 95%."
    )
    return text


def dataframe_to_excel_bytes(sheets: dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, data in sheets.items():
            safe_name = sheet_name[:31]
            data.to_excel(writer, sheet_name=safe_name, index=False)
    return output.getvalue()


st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

with st.sidebar:
    st.header("Pengaturan Data")
    data_mode = st.radio("Sumber data", ["Gunakan data contoh", "Upload file sendiri"])
    st.info("Format data yang disarankan: satu kolom kelompok/formula dan satu atau lebih kolom numerik hasil pengukuran.")

if data_mode == "Gunakan data contoh":
    df = load_example_data()

else:
    uploaded = st.sidebar.file_uploader(
        "Upload file data",
        type=["csv", "xlsx"]
    )

    if uploaded is None:
        st.warning("Upload file CSV atau Excel terlebih dahulu, atau gunakan data contoh.")
        st.stop()

    file_name = uploaded.name.lower()

    try:
        if file_name.endswith(".csv"):
            df = pd.read_csv(
                uploaded,
                sep=None,
                engine="python",
                encoding="utf-8-sig"
            )

        elif file_name.endswith(".xlsx"):
            excel_file = pd.ExcelFile(uploaded)

            selected_sheet = st.sidebar.selectbox(
                "Pilih sheet Excel",
                excel_file.sheet_names
            )

            df = pd.read_excel(
                excel_file,
                sheet_name=selected_sheet
            )

        else:
            st.error("Format file belum didukung. Gunakan CSV atau Excel (.xlsx).")
            st.stop()

    except Exception:
        st.error("File tidak dapat dibaca. Pastikan format data sudah benar.")
        st.stop()

st.subheader("1. Preview Data")
st.dataframe(df, use_container_width=True)

st.subheader("🤖 2. Analisis Data dengan AI")

pertanyaan_ai = st.text_area(
    "Tulis pertanyaan untuk AI:",
    "Berikan ringkasan, temuan penting, masalah data jika ada, dan kesimpulan dari data ini."
)

if st.button("Analisis dengan AI"):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        ringkasan_data = f"""
        Jumlah baris: {df.shape[0]}
        Jumlah kolom: {df.shape[1]}
        Nama kolom: {list(df.columns)}

        Contoh 10 data pertama:
        {df.head(10).to_string()}

        Statistik ringkas:
        {df.describe(include='all').to_string()}
        """

        prompt = f"""
        Anda adalah asisten analis data farmasi/apotek.

        Analisis data berikut dengan bahasa Indonesia yang jelas, singkat, dan mudah dipahami.

        Data:
        {ringkasan_data}

        Pertanyaan pengguna:
        {pertanyaan_ai}

        Buat jawaban dengan format:
        1. Ringkasan data
        2. Temuan penting
        3. Masalah pada data jika ada
        4. Kesimpulan
        5. Saran singkat
        """

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )

        st.success("Analisis AI berhasil dibuat.")
        st.write(response.output_text)

    except Exception as e:
        st.error(f"Terjadi error saat memanggil AI: {e}")

if df.empty:
    st.error("Data kosong. Periksa kembali file CSV Anda.")
    st.stop()

categorical_cols = [c for c in df.columns if df[c].dtype == "object" or df[c].nunique() <= 20]
numeric_candidates = []
for c in df.columns:
    converted = pd.to_numeric(df[c], errors="coerce")
    if converted.notna().sum() >= 3:
        numeric_candidates.append(c)

if not categorical_cols or not numeric_candidates:
    st.error("Data belum memiliki kolom kelompok dan kolom numerik yang cukup untuk dianalisis.")
    st.stop()

col_a, col_b = st.columns(2)
with col_a:
    group_col = st.selectbox("Pilih kolom kelompok/formula", categorical_cols)
with col_b:
    value_col = st.selectbox("Pilih kolom parameter numerik", numeric_candidates)

analysis_df = df[[group_col, value_col]].copy()
analysis_df[value_col] = clean_numeric(analysis_df[value_col])
analysis_df = analysis_df.dropna()

if analysis_df[group_col].nunique() < 2:
    st.error("Minimal harus ada 2 kelompok untuk uji beda.")
    st.stop()

st.subheader("2. Statistik Deskriptif")
desc = descriptive_table(analysis_df, group_col, value_col)
st.dataframe(desc, use_container_width=True)

plot_left, plot_right = st.columns(2)
with plot_left:
    st.pyplot(make_boxplot(analysis_df, group_col, value_col))
with plot_right:
    st.pyplot(make_barplot(desc, group_col, value_col))

st.subheader("3. Uji Asumsi")
shapiro_df = shapiro_by_group(analysis_df, group_col, value_col)
st.write("**Uji normalitas Shapiro-Wilk per kelompok**")
st.dataframe(shapiro_df, use_container_width=True)

levene_stat, levene_p, levene_conclusion = levene_test(analysis_df, group_col, value_col)
levene_df = pd.DataFrame([{
    "uji": "Levene",
    "statistik": levene_stat,
    "p-value": levene_p,
    "kesimpulan": levene_conclusion,
}])
st.write("**Uji homogenitas varians Levene**")
st.dataframe(levene_df, use_container_width=True)

normal_all = (shapiro_df["p-value"].dropna() >= 0.05).all() if not shapiro_df["p-value"].dropna().empty else False
homogeneous = not pd.isna(levene_p) and levene_p >= 0.05

st.subheader("4. Uji Beda Otomatis")
if normal_all and homogeneous:
    test_name = "One-Way ANOVA"
    main_stat, main_p = one_way_anova(analysis_df, group_col, value_col)
    st.success("Data memenuhi asumsi normalitas dan homogenitas. Uji utama yang dipilih: One-Way ANOVA.")
elif normal_all and not homogeneous:
    test_name = "Kruskal-Wallis"
    main_stat, main_p = kruskal_test(analysis_df, group_col, value_col)
    st.warning("Data normal tetapi tidak homogen. Untuk menjaga aplikasi tetap sederhana dan aman, uji utama diarahkan ke Kruskal-Wallis. Pada naskah ilmiah, Anda dapat mempertimbangkan Welch ANOVA bila sesuai.")
else:
    test_name = "Kruskal-Wallis"
    main_stat, main_p = kruskal_test(analysis_df, group_col, value_col)
    st.warning("Data tidak memenuhi asumsi normalitas pada semua kelompok. Uji utama yang dipilih: Kruskal-Wallis.")

main_result = pd.DataFrame([{
    "uji": test_name,
    "statistik": main_stat,
    "p-value": main_p,
    "kesimpulan": significance_text(main_p),
}])
st.dataframe(main_result, use_container_width=True)

st.subheader("5. Analisis Lanjutan/Post Hoc")
posthoc_df = pd.DataFrame()
if main_p < 0.05:
    if test_name == "One-Way ANOVA":
        st.write("Karena hasil uji utama signifikan, aplikasi menjalankan **Tukey HSD**.")
        posthoc_df = tukey_posthoc(analysis_df, group_col, value_col)
    else:
        st.write("Karena hasil uji utama signifikan, aplikasi menjalankan **pairwise Mann-Whitney dengan koreksi Bonferroni** sebagai tindak lanjut nonparametrik sederhana.")
        posthoc_df = mannwhitney_pairwise(analysis_df, group_col, value_col)
    st.dataframe(posthoc_df, use_container_width=True)
else:
    st.info("Post hoc tidak dijalankan karena hasil uji utama tidak signifikan.")

st.subheader("6. Narasi Hasil Otomatis")
narrative = generate_narrative(
    group_col=group_col,
    value_col=value_col,
    desc=desc,
    shapiro_df=shapiro_df,
    levene_result=(levene_stat, levene_p, levene_conclusion),
    main_test_name=test_name,
    main_stat=main_stat,
    main_p=main_p,
)
st.text_area("Narasi siap diedit untuk laporan/artikel", narrative, height=180)

st.subheader("7. Export Hasil")
export_sheets = {
    "data_bersih": analysis_df,
    "deskriptif": desc,
    "shapiro": shapiro_df,
    "levene": levene_df,
    "uji_utama": main_result,
}
if not posthoc_df.empty:
    export_sheets["posthoc"] = posthoc_df

excel_bytes = dataframe_to_excel_bytes(export_sheets)
st.download_button(
    label="Download hasil analisis Excel",
    data=excel_bytes,
    file_name=f"hasil_analisis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.download_button(
    label="Download narasi TXT",
    data=narrative.encode("utf-8"),
    file_name=f"narasi_hasil_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
    mime="text/plain",
)

with st.expander("Catatan interpretasi"):
    st.markdown(
        """
        - P-value < 0,05 menunjukkan hasil signifikan secara statistik.
        - Shapiro-Wilk digunakan untuk mengecek normalitas tiap kelompok.
        - Levene digunakan untuk mengecek kesamaan varians antar kelompok.
        - One-Way ANOVA digunakan bila data normal dan homogen.
        - Kruskal-Wallis digunakan bila asumsi parametrik tidak terpenuhi.
        - Narasi otomatis tetap perlu disesuaikan dengan konteks penelitian dan arahan dosen/pembimbing.
        """
    )
