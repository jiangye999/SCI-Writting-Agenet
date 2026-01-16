# Methods

## Study Design

This retrospective study analyzed mammographic data from five academic medical centers collected between January 2018 and December 2022. The study protocol was approved by the Institutional Review Board at each participating institution, with a waiver of informed consent due to the retrospective nature of the analysis.

## Dataset

The dataset comprised 14,000 mammographic examinations from 12,456 unique patients. All images were acquired using digital mammography systems from three major manufacturers (Hologic, GE, and Siemens). The study cohort included 4,900 biopsy-proven malignant cases and 9,100 negative controls. Images were randomly divided into training (10,000), validation (2,000), and test (2,000) sets, ensuring no patient overlap between sets. Two board-certified radiologists independently annotated all malignant lesions, with a third radiologist resolving discrepancies.

## Deep Learning Model

We developed a deep learning system based on a modified ResNet-50 architecture with attention mechanisms. The model was pre-trained on ImageNet and subsequently fine-tuned on our mammography dataset. Key modifications included: (1) replacing the final fully connected layer with a attention-based pooling module; (2) adding a branch for lesion localization; and (3) incorporating a interpretability module that generates heatmaps highlighting regions of interest.

Training was performed using the Adam optimizer with an initial learning rate of 1e-4, reduced by a factor of 10 when validation loss plateaued. Data augmentation included random flipping, rotation, and intensity adjustments. Models were trained for 50 epochs with early stopping based on validation AUC.

## Statistical Analysis

Model performance was evaluated using area under the receiver operating characteristic curve (AUC), sensitivity, specificity, and diagnostic accuracy. Confidence intervals were calculated using the DeLong method. Comparison between models was performed using McNemar's test. All statistical analyses were conducted using Python (version 3.9) with scikit-learn and scipy libraries.
