bArr = [15, 1, 22, 4, 57, 115, 54, 119, 29, 17, 55, 18, 113, 48, 29, 113,
        35, 49, 59, 29, 54, 114, 29, 4, 115, 44, 38, 29, 17, 113, 33, 48,
        39, 54, 119, 63]

key = 66

decoded_bytes = bytes([b ^ key for b in bArr])
flag = decoded_bytes.decode('utf-8')

print(flag)
