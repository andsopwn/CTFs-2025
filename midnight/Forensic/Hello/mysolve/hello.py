def xor_decode_file(input_path, output_path, key=0x42):
    with open(input_path, "rb") as f:
        encrypted_data = f.read()

    # 각 바이트를 key(0x42)와 XOR
    decoded_data = bytearray(b ^ key for b in encrypted_data)

    with open(output_path, "wb") as f:
        f.write(decoded_data)

# 사용 예시
if __name__ == "__main__":
    xor_decode_file("CFcGFCGgn", "decoded_payload.bin", 0x42)
