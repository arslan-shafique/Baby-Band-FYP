import tensorflow as tf

# =========================
# LOAD MODEL
# =========================
MODEL_PATH = "cnn_model_fixed.tflite"

interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

print("\n==============================")
print("MODEL LOADED SUCCESSFULLY")
print("==============================")

# =========================
# PRINT OPERATORS
# =========================
print("\n=== OPERATOR LIST ===")

ops = []
for op in interpreter._get_ops_details():
    op_name = op['op_name']
    ops.append(op_name)
    print(op_name)

# =========================
# CHECK FOR FORBIDDEN OPS
# =========================
forbidden_ops = {"STRIDED_SLICE", "SHAPE", "PACK", "GATHER", "MEAN"}

found_forbidden = set(ops).intersection(forbidden_ops)

print("\n=== VALIDATION RESULT ===")

if len(found_forbidden) > 0:
    print("❌ MODEL NOT COMPATIBLE WITH ESP32")
    print("Found forbidden ops:")
    for f in found_forbidden:
        print(" -", f)
else:
    print("✅ MODEL OPERATOR SET IS CLEAN (ESP32 READY)")

# =========================
# CHECK INPUT / OUTPUT SHAPES
# =========================
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("\n=== INPUT / OUTPUT DETAILS ===")

print("Input shape :", input_details[0]['shape'])
print("Output shape:", output_details[0]['shape'])

# =========================
# CHECK EXPECTED INPUT SHAPE
# =========================
expected_shapes = [
    [1, 128, 13, 1],
    [128, 13, 1],
    [1, 128, 39, 1]  # Added our new V1 shape here!
]

input_shape = list(input_details[0]['shape'])

print("\n=== SHAPE VALIDATION ===")

if input_shape in expected_shapes:
    print("✅ Input shape is correct")
else:
    print("⚠️ Input shape mismatch!")
    print("Expected:", expected_shapes)
