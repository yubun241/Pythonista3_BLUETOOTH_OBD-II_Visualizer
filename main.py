import cb
import time

class OBDTester(object):
    def __init__(self):
        self.peripheral = None
        self.characteristic = None
        self.found = False

    def did_discover_peripheral(self, p):
        if not self.found and p.name:
            print(f'デバイス発見: {p.name} [{p.uuid}]')
            # OBD, V-LINK, LELink, ELM などが含まれる名前を探す
            if 'OBD' in p.name.upper() or 'V-LINK' in p.name.upper():
                print('--> ターゲットを発見しました。接続します...')
                self.found = True
                self.peripheral = p
                cb.connect_peripheral(p)

    def did_connect_peripheral(self, p):
        print('接続完了！サービスを探索中...')
        p.discover_services()

    def did_discover_services(self, p, error):
        if error:
            print(f'サービス探索エラー: {error}')
            return
        for s in p.services:
            print(f'サービス発見: {s.uuid}')
            # 一般的なシリアル通信サービス(FFE0など)を探す
            p.discover_characteristics(s)

    def did_discover_characteristics(self, s, error):
        for c in s.characteristics:
            print(f'  特性(Char)発見: {c.uuid} (Properties: {c.properties})')
            # 書き込み可能な特性を保持
            self.characteristic = c
            # 通知を有効にする
            self.peripheral.set_notify_value(c, True)
            
        # 通信テスト開始
        self.test_communication()

    def test_communication(self):
        print('\n--- コマンド送信テスト ---')
        # 1. リセット
        self.send('ATZ')
        time.sleep(1)
        # 2. エコーオフ
        self.send('ATE0')
        time.sleep(0.5)
        # 3. RPM要求 (01 0C)
        print('RPM取得テスト(010C)送信...')
        self.send('010C')

    def send(self, cmd):
        if self.peripheral and self.characteristic:
            full_cmd = (cmd + '\r').encode('ascii')
            self.peripheral.write_characteristic_value(self.characteristic, full_cmd, True)
            print(f'送信済: {cmd}')

    def did_update_value(self, c, error):
        payload = c.value.decode('ascii', errors='ignore').strip()
        print(f'>> 受信データ: {payload}')

    def did_fail_to_connect_peripheral(self, p, error):
        print(f'接続失敗: {error}')

    def did_disconnect_peripheral(self, p, error):
        print('切断されました')

# 実行
tester = OBDTester()
cb.set_central_delegate(tester)
print('BLEスキャン開始...')
cb.scan_for_peripherals()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cb.reset()
    print('スキャン停止')
