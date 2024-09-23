import can
import pandas as pd

# 사용자로부터 BLF 파일명을 입력받기
blf_file = input("BLF 파일명을 입력하세요: ")

# BLF 파일을 읽기
log = can.BLFReader(blf_file)

# 데이터를 pandas DataFrame으로 변환
data = []
for msg in log:
    data.append({
        'Timestamp': msg.timestamp,
        'Channel': msg.channel,
        'Arbitration ID': msg.arbitration_id,
        'Data': msg.data.hex()
    })

df = pd.DataFrame(data)

# CSV 파일로 저장
csv_file = blf_file.replace('.BLF', '.csv')
df.to_csv(csv_file, index=False)

print(f"데이터가 {csv_file}로 저장되었습니다.")

