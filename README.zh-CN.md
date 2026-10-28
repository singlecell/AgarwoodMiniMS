# AgarwoodMiniMS

沉香质谱分类软件，支持随机森林、SVM、KNN、朴素贝叶斯和 GBDT。

[English](README.md)

## 研究背景

本研究将纸毛细管喷雾与微型质谱结合，用于沉香的现场快速鉴别。将粉末样品置于色谱纸上，加入溶剂提取，再通过便携式微型质谱仪分析。论文报道分析流程约需 1 分钟，并利用质谱指纹和随机森林模型区分沉香、奇楠及伪品。

AgarwoodMiniMS 提供这一流程中的数据分析功能：对整理后的质谱 CSV 数据进行模型训练和类别预测。软件附带论文 DEMO 数据，支持随机森林、SVM、KNN、朴素贝叶斯和梯度提升模型。

![纸毛细管喷雾微型质谱用于沉香现场快速鉴别的流程](docs/images/paper-figure1.png)

图源：[Xie 等，Journal of Analysis and Testing（2025）](https://doi.org/10.1007/s41664-024-00331-0)，图 1，展示采样、便携式质谱检测及分类流程。

## DEMO 运行结果

![六个 DEMO 样本的随机森林预测结果](docs/images/demo-rf-predictions.png)

使用随机森林（`rf`）和默认 `legacy` 划分，以 `demo_train.csv` 训练、对 `demo_predict.csv` 预测后，程序实际导出的结果。各子图标题为预测类别，DEMO 质谱数据来自下方引用的研究。

## 安装与启动

Windows 版：完整解压后双击 `AgarwoodMiniMS.exe`，保留 `_internal` 文件夹。

源码版：安装 Python 3.11 或以上，在项目目录运行：

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install .
agarwood-minims gui
```

## 用 DEMO 试运行

1. 保留默认 `rf` 和 `legacy`，点击 **Train and evaluate**。
2. 选择 `demo/demo_train.csv`，再选择结果保存目录。
3. 点击 **Predict and save spectra**，选择刚生成的 `model.joblib`，确认来源可信。
4. 选择 `demo/demo_predict.csv`，指定新的结果文件名。

程序会导出预测 CSV 和质谱 PNG。

## 换成自己的数据

参照 DEMO 格式准备 CSV：`Sample` 为样本编号，数值型 m/z 列为强度，训练表还需 `Label` 列。

用自己的训练表重新训练，再选择自己的预测表。两张表的质谱特征须一致。需要尝试其他算法时，在界面中选择后重新训练即可。

## 论文引用

在研究中使用本软件或 DEMO 数据时，请引用：

Xie, Y., Huang, S., Zhang, Q., et al. On-Site Analysis and Rapid Authentication of Valuable Agarwood Samples by Paper Capillary Spray Miniature Mass Spectrometry. *Journal of Analysis and Testing* **9**, 61–70 (2025). [https://doi.org/10.1007/s41664-024-00331-0](https://doi.org/10.1007/s41664-024-00331-0)
