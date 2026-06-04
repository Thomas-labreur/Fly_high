import pandas as pd
import numpy as np

class DataProcessor:

    def _coerce_numeric_cols(self, df):
        for col in ["Age (days)", "Trial", "point ID"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def table_to_df(self, table_widget, all_columns) -> pd.DataFrame:
        rows = []
        for row in range(table_widget.rowCount()):
            r = {}
            for col, name in enumerate(all_columns):
                item = table_widget.item(row, col)
                r[name] = item.text() if item else ""
            rows.append(r)
        df = pd.DataFrame(rows, columns=all_columns)
        df["Height (cm)"] = pd.to_numeric(df["Height (cm)"], errors="coerce")
        df = self._coerce_numeric_cols(df)
        return df

    def tube_by_trial(self, df):
        """Stats par ROI et par trial (mode group tubes)."""
        if df.empty or "Height (cm)" not in df.columns:
            return pd.DataFrame()
        group_cols = [c for c in ["Cohort", "Genotype", "Condition", "Age (days)", "Sex", "Trial", "ROI name"] if c in df.columns]
        out = df.groupby(group_cols, dropna=False)["Height (cm)"].agg(
            n="count",
            mean_height_cm="mean",
            median_height_cm="median",
            sd_hieght_cm="std",
            q1_height_cm=lambda x: x.quantile(0.25),
            q3__height_cm=lambda x: x.quantile(0.75),
        ).reset_index()
        out["iqr_height_cm"] = out["q3_height_cm"] - out["q1_height_cm"]
        return out

    def single_trial_values(self, df):
        """Une ligne par fly par trial (mode single flies uniquement)."""
        if df.empty or "Fly ID" not in df.columns:
            return pd.DataFrame()
        tmp = df.copy()
        if "Assay mode" in tmp.columns:
            tmp = tmp[tmp["Assay mode"].astype(str).str.lower() == "single flies"]
        if tmp.empty:
            return pd.DataFrame()
        group_cols = [c for c in ["Cohort", "Genotype", "Condition", "Sex", "Fly ID", "Age (days)", "Trial"] if c in tmp.columns]
        out = tmp.groupby(group_cols, dropna=False).agg(
            height_cm=("Height (cm)", "mean"),
            n_detections=("Height (cm)", "count"),
            roi_name=("ROI name", "first"),
        ).reset_index()
        return out.sort_values([c for c in ["Fly ID", "Age (days)", "Trial"] if c in out.columns])

    def single_by_fly_age(self, df):
        """Moyenne par fly par age (agrège les trials)."""
        trial = self.single_trial_values(df)
        if trial.empty:
            return pd.DataFrame()
        group_cols = [c for c in ["Cohort", "Genotype", "Condition", "Sex", "Fly ID", "Age (days)"] if c in trial.columns]
        out = trial.groupby(group_cols, dropna=False).agg(
            mean_height_cm=("height_cm", "mean"),
            median_height_cm=("height_cm", "median"),
            sd_across_trials_cm=("height_cm", "std"),
            n_trials=("height_cm", "count"),
            trials_present=("Trial", lambda x: ",".join(sorted(set(map(str, x))))),
            total_detections=("n_detections", "sum"),
        ).reset_index()
        return out.sort_values([c for c in ["Fly ID", "Age (days)"] if c in out.columns])

    def single_trajectories(self, df):
        """Wide : une ligne par fly, une colonne par age."""
        by = self.single_by_fly_age(df)
        if by.empty:
            return pd.DataFrame()
        idx_cols = [c for c in ["Fly ID", "Sex", "Cohort", "Genotype", "Condition"] if c in by.columns]
        wide = by.pivot_table(index=idx_cols, columns="Age (days)", values="mean_height_cm", aggfunc="mean").reset_index()
        wide.columns = [f"day_{c}" if c not in idx_cols else c for c in wide.columns]
        return wide

    def qc_trials_per_fly(self, df):
        """QC : nombre de trials par fly par age."""
        by = self.single_by_fly_age(df)
        if by.empty:
            return pd.DataFrame()
        cols = [c for c in ["Cohort", "Genotype", "Condition", "Sex", "Fly ID", "Age (days)", "n_trials", "trials_present", "total_detections"] if c in by.columns]
        return by[cols]

    def figure_points_long(self, df):
        """Toutes les mesures brutes, colonnes utiles seulement."""
        if df.empty:
            return pd.DataFrame()
        keep = [c for c in ["Age (days)", "Height (cm)", "Fly ID", "ROI name", "Trial", "Sex", "Cohort", "Genotype", "Condition", "Assay mode", "Filename", "Frame"] if c in df.columns]
        return df[keep].copy().sort_values([c for c in ["Age (days)", "Fly ID", "ROI name", "Trial"] if c in df.columns])

    def figure_points_wide(self, df):
        """Wide : une colonne par age, toutes les hauteurs brutes."""
        if df.empty or "Age (days)" not in df.columns or "Height (cm)" not in df.columns:
            return pd.DataFrame()
        ages = sorted(df["Age (days)"].dropna().unique(), key=lambda x: float(x) if str(x).replace('.','').isdigit() else x)
        cols, max_len = {}, 0
        for age in ages:
            vals = df.loc[df["Age (days)"].astype(str) == str(age), "Height (cm)"].reset_index(drop=True)
            cols[f"day_{age}"] = vals
            max_len = max(max_len, len(vals))
        return pd.DataFrame({k: v.reindex(range(max_len)) for k, v in cols.items()})

    def upper_dispersion(self, values):
        vals = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy()
        if len(vals) == 0:
            return np.nan
        mean = vals.mean()
        upper = vals[vals > mean] - mean
        return 0.0 if len(upper) == 0 else float(np.sqrt(np.mean(upper ** 2)))

    def figure_dispersion(self, df):
        """Dispersion des hauteurs brutes par age."""
        if df.empty or "Age (days)" not in df.columns:
            return pd.DataFrame()
        rows = []
        for age, g in df.groupby("Age (days)", dropna=False):
            vals = g["Height (cm)"].dropna()
            if len(vals) == 0:
                continue
            mean = float(vals.mean())
            upper = self.upper_dispersion(vals)
            rows.append({
                "Age (days)": age, "n_measurements": int(len(vals)),
                "mean_height_cm": mean, "median_cm": float(vals.median()),
                "sd_height_cm": float(vals.std(ddof=1)) if len(vals) > 1 else np.nan,
                "q1_height_cm": float(vals.quantile(0.25)), "q3_cm": float(vals.quantile(0.75)),
                "iqr_height_cm": float(vals.quantile(0.75) - vals.quantile(0.25)),
                "upper_dispersion_height_cm": upper,
                "relative_upper_dispersion": upper / mean if mean > 0 else np.nan,
            })
        return pd.DataFrame(rows)

    def single_boxplot_wide(self, df):
        """Wide : une colonne par age, une ligne par fly (moyenne des trials)."""
        by = self.single_by_fly_age(df)
        if by.empty:
            return pd.DataFrame()
        ages = sorted(by["Age (days)"].dropna().unique(), key=lambda x: float(x) if str(x).replace('.','').isdigit() else x)
        cols, max_len = {}, 0
        for age in ages:
            vals = by.loc[by["Age (days)"].astype(str) == str(age), "mean_height_cm"].reset_index(drop=True)
            cols[f"day_{age}"] = vals
            max_len = max(max_len, len(vals))
        return pd.DataFrame({k: v.reindex(range(max_len)) for k, v in cols.items()})

    def single_dispersion(self, df):
        """Dispersion des moyennes par fly par age."""
        by = self.single_by_fly_age(df)
        if by.empty:
            return pd.DataFrame()
        tmp = by.rename(columns={"mean_height_cm": "Height (cm)"})
        return self.figure_dispersion(tmp)

    def all_sheets(self, table_widget, all_columns) -> dict:
        df = self.table_to_df(table_widget, all_columns)
        return {
            "raw_data":            df,
            "tube_by_trial":       self.tube_by_trial(df),
            "single_trial_values": self.single_trial_values(df),
            "single_by_fly_age":   self.single_by_fly_age(df),
            "single_trajectories": self.single_trajectories(df),
            "qc_trials_per_fly":   self.qc_trials_per_fly(df),
            "figure_points_long":  self.figure_points_long(df),
            "figure_points_wide":  self.figure_points_wide(df),
            "figure_dispersion":   self.figure_dispersion(df),
            "single_boxplot_wide": self.single_boxplot_wide(df),
            "single_dispersion":   self.single_dispersion(df),
        }