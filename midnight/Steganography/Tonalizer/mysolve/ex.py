import wave
import numpy as np
import math

WAV_FILE = "tonalizer.wav"
CHUNK_DURATION = 0.05 

TOP_N = 5 

def find_top_frequencies(audio_chunk, sample_rate, top_n=5):
    window = np.hanning(len(audio_chunk))
    windowed = audio_chunk * window
    
    # FFT
    fft_data = np.fft.rfft(windowed)
    mag = np.abs(fft_data)
    
    freqs = np.fft.rfftfreq(len(windowed), 1.0 / sample_rate)
    
    top_indices = np.argsort(mag)[-top_n:]  
    top_indices = top_indices[np.argsort(mag[top_indices])[::-1]]
    
    result = []
    for idx in top_indices:
        freq_val = freqs[idx]
        amplitude = mag[idx]
        result.append((freq_val, amplitude))
    
    return result

def main():
    with wave.open(WAV_FILE, 'rb') as w:
        nchannels = w.getnchannels()
        sampwidth = w.getsampwidth()
        sample_rate = w.getframerate()
        nframes = w.getnframes()
        
        raw_data = w.readframes(nframes)

    data = np.frombuffer(raw_data, dtype=np.int16)
    if nchannels > 1:
        data = data[0::nchannels]
    
    total_samples = len(data)
    chunk_size = int(sample_rate * CHUNK_DURATION)
    
    print(f"Total samples = {total_samples}, sample_rate = {sample_rate}")
    print(f"Chunk size = {chunk_size} samples (~{CHUNK_DURATION} sec)")

    i = 0
    chunk_idx = 0
    results = []
    
    while i < total_samples:
        chunk = data[i : i + chunk_size]
        if len(chunk) < chunk_size:
            pass
        
        top_freqs = find_top_frequencies(chunk, sample_rate, TOP_N)
        
        results.append((chunk_idx, top_freqs))
        
        chunk_idx += 1
        i += chunk_size
    
    for (idx, freqs_info) in results:
        freq_str = ", ".join(f"{f:.1f}Hz({m:.0f})" for f,m in freqs_info)
        print(f"Chunk {idx}: {freq_str}")

if __name__ == "__main__":
    main()
