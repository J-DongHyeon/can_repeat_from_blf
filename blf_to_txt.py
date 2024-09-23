import can

# BLF 파일에서 CAN 메시지를 읽고 txt 파일로 변환하는 함수
def convert_blf_to_txt(blf_file, txt_file):
    # BLF 파일 읽기
    log = can.BLFReader(blf_file)
    
    # 텍스트 파일로 변환
    with open(txt_file, 'w') as f:
        for msg in log:
            # CAN ID를 16진수 문자열로 변환 (8자리 고정)
            can_id = format(msg.arbitration_id, '08X')
            
            # CAN 데이터를 16진수 문자열로 변환 (2자리씩)
            can_data = ''.join(format(byte, '02X') for byte in msg.data)
            
            # {can id}#{can data} 형식으로 작성
            line = f"{can_id}#{can_data}\n"
            
            # 파일에 작성
            f.write(line)

    print(f"BLF 파일 '{blf_file}'이(가) '{txt_file}'로 변환되었습니다.")

# BLF 파일 경로와 출력할 TXT 파일 경로
blf_file = '/home/aiden/tm_ws/can_repeat_from_blf/blf_files/E25_EXMS_01_can2_20240828_123000__20240828_125959.BLF'
txt_file = 'E25_EXMS_01_can2_20240828_123000__20240828_125959.txt'

# 변환 함수 실행
convert_blf_to_txt(blf_file, txt_file)

