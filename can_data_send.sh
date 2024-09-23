#!/bin/bash

# 입력 파일 경로
input_file="txt_files/E25_EXMS_01_can2_20240827_140000__20240827_142959.txt"

# 파일이 존재하는지 확인
if [ ! -f "$input_file" ]; then
    echo "입력 파일이 존재하지 않습니다: $input_file"
    exit 1
fi

# can0 인터페이스 상태 확인
check_can0_status() {
    status=$(ip -details link show can0 | grep -o 'can state [A-Z-]*' | awk '{print $3}')
    if [ "$status" == "ERROR-PASSIVE" ]; then
        echo "CAN0 is ERROR-PASSIVE. Running can0_intf.sh..."
        ./can0_intf.sh start
    fi

    if [ "$status" == "BUS-OFF" ]; then
        echo "CAN0 is BUS-OFF. Running can0_intf.sh..."
        ./can0_intf.sh start
    fi
}

# 입력 파일을 읽고 명령어를 실행
while IFS=# read -r can_id data; do
    # can0 상태 확인 및 필요 시 재설정
    check_can0_status

    # cansend 명령어 실행
    cansend can0 "${can_id}#${data}"
    echo "cansend can0 ${can_id}#${data}"

    # 0.002초 대기    
    sleep 0.002
done < "$input_file"

echo "모든 명령어가 실행되었습니다."