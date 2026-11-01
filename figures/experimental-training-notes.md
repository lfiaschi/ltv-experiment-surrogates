# Experimental training workflow

Source: Day et al., sections 3.1–3.2, DOI10.1145/3770854.3783922.
Purpose: distinguish training with historical randomized assignments from
scoring a new experiment with observed early features.

Z is historical random assignment, W is pre-experiment information, X is the
observed early-feature vector and Y is the later individual outcome. During
training, h(Z,W) predicts X. The second stage fits g(predictedX,W) to observedY.
At scoring, g receives actualX and W. It predicts an individual future outcome,
not a treatment effect. The dashed connector means reuse of a trained model.
No historical or new assignment indicators are scoring inputs.

Generated directly with Nano Banana Pro from the adjacent prompt. The delivered
JPEG bytes were converted to PNG. The title/labels and all six boxes were
visually checked against these relationships. Inspect at375px viewport; avoid
shrinking long labels to add extra prose.
