# AgarwoodMiniMS

沉香质谱分类软件，支持随机森林、SVM、KNN、朴素贝叶斯和 GBDT。

## 启动

完整解压后双击 `AgarwoodMiniMS.exe`，无需安装 Python。请保留 `_internal` 文件夹。

## 用 DEMO 试运行

1. 保留默认 `rf` 和 `legacy`，点击 **Train and evaluate**。
2. 选择 `demo/demo_train.csv`，再选择结果保存目录。
3. 点击 **Predict and save spectra**，选择刚生成的 `model.joblib`，确认来源可信。
4. 选择 `demo/demo_predict.csv`，指定新的结果文件名。

程序会导出预测 CSV 和质谱 PNG。

## 换成自己的数据

参照 DEMO 格式准备 CSV：`Sample` 为样本编号，数值型 m/z 列为强度，训练表还需 `Label` 列。

用自己的训练表重新训练，再选择自己的预测表。两张表的质谱特征须一致。需要尝试其他算法时，在界面中选择后重新训练即可。
