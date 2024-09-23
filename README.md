# can_repeat_from_blf


#### blf 파일로부터 can 데이터를 발행하는 방법은 2가지가 있다.

1. `reader_blf.py` 실행
  `reader_blf.py` 코드는 blf 파일을 읽어 can 데이터로 발행해주는 코드이다.
  blf 파일의 모든 can 데이터를 재생하지는 않고, 원하는 can id 만 필터링하여 재생한다.
  blf 파일 명과, 필터링 하는 can id 는 하드코딩 되어있다.

  ```
  python3 can_library/can_library/examples/reader_blf.py
  ```

2. 현재 발행하는 can raw 데이터 decode
	필요 시, 현재 발행 중인 can raw 데이터를 decode 하여 출력할 수 있다.
  decode 에 기반이 되는 dbc 파일 명은 코드에 하드코딩 해주어야 한다.
  PyCanTools 관련 주석 부분을 해제하면 된다.

---

1. blf -> txt 파일로 변환
  다음의 명령어로 blf 파일을 txt 파일로 변환한다.
  blf 파일명 및 txt 파일명은 하드코딩 되어있다.

  ```
  python3 blf_to_txt.py
  ```

2. can 데이터 발행
  다음의 sh 코드를 이용하여 can 데이터를 발행한다.
  PC 의 can 포트가 BUS-OFF 또는 ERROR-PASSIVE 가 되는 경우, can 포트 상태를 재설정하는 코드가 포함되어 있다.
  참조하는 txt 파일 명은 sh 코드 내부에 하드코딩 되어 있다.

  ```
  . can_data_send.sh
  ```


#### 참고

- can 포트 활성화
```
sudo ip link set can0 up type can bitrate 250000
```

- can 포트 상태 확인
```
ip -details link show can0
```

- can 포트 재설정
```
. can0_intf.sh start
```

- blf -> csv 파일 변환
```
python3 blf_to_csv.py
```


