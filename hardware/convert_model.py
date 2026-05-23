import sys

model_path = "../ml_model/cry_detection/models/cry_detection/cnn_model_fixed.tflite"
output_path = "model_data.h"

with open(model_path, "rb") as f:
    model = f.read()

with open(output_path, "w") as f:
    f.write("const unsigned char cnn_model_tflite[] = {")
    
    for i, byte in enumerate(model):
        if i % 12 == 0:
            f.write("\n ")
        f.write("0x{:02x}, ".format(byte))
    
    f.write("\n};\n")
    f.write("const unsigned int cnn_model_tflite_len = {};\n".format(len(model)))

print("Conversion complete!")