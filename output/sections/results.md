# Results

## Model Performance

The developed deep learning model achieved an AUC of 0.94 (95% CI: 0.93-0.95) on the independent test set. At the optimal operating point (sensitivity 91.2%, specificity 88.7%), the overall diagnostic accuracy was 89.8%. Table 1 presents the detailed performance metrics across different operating thresholds.

Compared to the baseline ResNet-50 model without attention mechanisms, our modified architecture showed significant improvement in AUC (0.94 vs. 0.89, p<0.001). The attention-based pooling module contributed to a 2.3% increase in sensitivity at high specificity levels, particularly for detecting subtle lesions.

## Comparison with Radiologists

In a reader study involving 5 experienced radiologists, the AI system demonstrated superior performance to 3 of 5 radiologists and comparable performance to the remaining 2. The average radiologist AUC was 0.87 (95% CI: 0.84-0.90), significantly lower than the AI system (p=0.002). Notably, when AI assistance was provided, radiologist performance improved significantly (AUC increase from 0.87 to 0.92, p=0.01), with the greatest improvement observed among less experienced readers.

## Subgroup Analysis

Performance was consistent across different manufacturers (Hologic: AUC 0.94; GE: AUC 0.93; Siemens: AUC 0.94). The model maintained high performance across all breast density categories, though slightly lower AUC was observed in extremely dense breasts (0.91 vs. 0.95 in fatty breasts). Age-stratified analysis revealed consistent performance across all age groups.

## Interpretability Assessment

The heatmap visualization module correctly localized malignant lesions in 93.4% of cases. Independent review by radiologists found that 87.6% of generated heatmaps were rated as clinically acceptable for aiding diagnosis. Furthermore, the attention weights showed high correlation with radiologist annotations (Dice coefficient: 0.82).
