from weather_dashboard.loaders.bias_report_loader import BiasReportLoader


def test_bias_report_loader(tmp_path):
    path = tmp_path / "bias.csv"
    path.write_text("metric,value\nmae,0.8\nrmse,1.1\n", encoding="utf-8")

    loader = BiasReportLoader()
    df = loader.load_df(path)

    assert len(df) == 2
    assert df.iloc[0]["metric"] == "mae"
