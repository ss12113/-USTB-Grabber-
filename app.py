import sys
import json
import requests
import urllib3
import os
from PySide6.QtCore import QUrl, Slot, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QFormLayout, QMessageBox, QLabel,
    QSplitter, QGroupBox, QListWidget, QListWidgetItem, QSpinBox,
    QComboBox  # <--- 新增导入 QComboBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====== 基础配置 ======
LOGIN_URL = "https://byyt.ustb.edu.cn/"
API_URL = "https://byyt.ustb.edu.cn/Xsxk/addGouwuche"

# 学期配置
DEFAULT_XN = "2025-2026"
DEFAULT_XQ = "2"
DEFAULT_XNXQ = "2025-20262"

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USTB 抢课神器 (多类型支持版)")
        self.resize(1300, 850)
        
        self.cookies = {}
        self.sess = requests.Session()
        self.target_course = None 
        self.exist_pids = set()
        
        # 确定数据文件保存路径
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.data_file = os.path.join(base_path, "courses_data.json")

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_request)
        
        self.setup_ui()
        
        # 浏览器配置
        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.web.page().profile().cookieStore().cookieAdded.connect(self.on_cookie_added)
        
        self.web.setUrl(QUrl(LOGIN_URL))

        # 🟢 启动时自动加载本地数据
        self.load_from_file()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # === 左侧：浏览器 ===
        web_group = QGroupBox("1. 浏览器登录")
        web_layout = QVBoxLayout(web_group)
        self.web = QWebEngineView()
        web_layout.addWidget(self.web)
        
        # === 右侧：控制台 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 2. JSON 导入区
        json_group = QGroupBox("2. 添加课程 (自动保存)")
        json_layout = QVBoxLayout(json_group)
        
        self.text_json = QTextEdit()
        self.text_json.setPlaceholderText("在此粘贴 queryKxrw 的 Response JSON...")
        self.text_json.setMaximumHeight(80)
        
        btn_layout = QHBoxLayout()
        btn_parse = QPushButton("➕ 解析并保存")
        btn_parse.clicked.connect(self.parse_and_append)
        
        btn_clear_input = QPushButton("清空输入框")
        btn_clear_input.clicked.connect(self.text_json.clear)
        
        btn_layout.addWidget(btn_parse)
        btn_layout.addWidget(btn_clear_input)
        
        json_layout.addWidget(self.text_json)
        json_layout.addLayout(btn_layout)
        right_layout.addWidget(json_group)
        
        # 3. 列表与控制
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        list_group = QGroupBox("3. 课程池")
        list_layout = QVBoxLayout(list_group)
        
        self.course_list_widget = QListWidget()
        self.course_list_widget.itemClicked.connect(self.on_course_selected)
        
        btn_clear_list = QPushButton("🗑️ 清空所有课程")
        btn_clear_list.clicked.connect(self.clear_all_courses)
        
        list_layout.addWidget(self.course_list_widget)
        list_layout.addWidget(btn_clear_list)
        
        control_group = QGroupBox("4. 操作台")
        control_layout = QFormLayout(control_group)
        
        self.lbl_target = QLineEdit("未选择")
        self.lbl_target.setReadOnly(True)
        self.lbl_target.setStyleSheet("color: blue; font-weight: bold;")

        # === 👇 新增：课程类型选择下拉框 👇 ===
        self.combo_type = QComboBox()
        # 格式：addItem("显示给用户看的文字", "实际传给服务器的值")
        self.combo_type.addItem("必修课 (bx-b-b)", "bx-b-b")
        self.combo_type.addItem("素质拓展 (sztzk-b-b)", "sztzk-b-b")
        self.combo_type.addItem("专业拓展 (zytzk-b-b)", "zytzk-b-b")
        # ====================================
        
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(100, 10000)
        self.spin_interval.setValue(500)
        self.spin_interval.setSuffix(" ms")
        self.spin_interval.setSingleStep(100)
        
        self.btn_start = QPushButton("🚀 启动循环")
        self.btn_start.setCheckable(True)
        self.btn_start.setStyleSheet("background-color: #d83b01; color: white; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self.toggle_grabbing)
        
        control_layout.addRow("目标:", self.lbl_target)
        control_layout.addRow("类型:", self.combo_type) # 把下拉框加进去
        control_layout.addRow("间隔:", self.spin_interval)
        control_layout.addRow(self.btn_start)
        
        middle_splitter.addWidget(list_group)
        middle_splitter.addWidget(control_group)
        middle_splitter.setStretchFactor(0, 2)
        middle_splitter.setStretchFactor(1, 1)
        right_layout.addWidget(middle_splitter, 1)
        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        right_layout.addWidget(self.log_box, 1)
        
        splitter_main = QSplitter(Qt.Orientation.Horizontal)
        splitter_main.addWidget(web_group)
        splitter_main.addWidget(right_panel)
        splitter_main.setStretchFactor(0, 1)
        splitter_main.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter_main)

    def save_to_file(self):
        all_courses = []
        for i in range(self.course_list_widget.count()):
            item = self.course_list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            all_courses.append(data)
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(all_courses, f, ensure_ascii=False, indent=4)
            self.log(f"💾 已保存")
        except Exception as e:
            self.log(f"⚠️ 保存失败: {e}")

    def load_from_file(self):
        if not os.path.exists(self.data_file): return
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                saved_courses = json.load(f)
            count = 0
            for data in saved_courses:
                pid = data.get('pid')
                if pid and pid not in self.exist_pids:
                    display = f"{data['name']} - {data.get('teacher','未知')} ({data['kcdm']})"
                    item = QListWidgetItem(display)
                    item.setData(Qt.ItemDataRole.UserRole, data)
                    self.course_list_widget.addItem(item)
                    self.exist_pids.add(pid)
                    count += 1
            if count > 0: self.log(f"📂 加载本地: {count} 门")
        except Exception as e:
            self.log(f"⚠️ 读取失败: {e}")

    def parse_and_append(self):
        json_str = self.text_json.toPlainText().strip()
        if not json_str: return
        try:
            if json_str.startswith("MY_CAPTURE:"): json_str = json_str.replace("MY_CAPTURE:", "")
            res = json.loads(json_str)
            course_data = []
            if "kxrwList" in res and isinstance(res["kxrwList"], dict):
                course_data = res["kxrwList"].get("list", [])
            elif "yxkcList" in res:
                course_data = res.get("yxkcList", [])
            elif isinstance(res, list):
                course_data = res
                
            new_count = 0
            for item in course_data:
                name = item.get("kcmc", "未知")
                pid = item.get("id", "")
                kcdm = item.get("kcdm", "")
                teacher = item.get("dgjsmc", "")
                if pid and kcdm and pid not in self.exist_pids:
                    display = f"{name} - {teacher} ({kcdm})"
                    list_item = QListWidgetItem(display)
                    list_item.setData(Qt.ItemDataRole.UserRole, {
                        "name": name, "pid": pid, "kcdm": kcdm, "teacher": teacher
                    })
                    self.course_list_widget.addItem(list_item)
                    self.exist_pids.add(pid)
                    new_count += 1
            self.log(f"✅ 新增 {new_count} 门")
            self.text_json.clear()
            self.save_to_file()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析失败: {e}")

    def clear_all_courses(self):
        self.course_list_widget.clear()
        self.exist_pids.clear()
        self.target_course = None
        self.lbl_target.setText("未选择")
        self.save_to_file()

    def on_course_selected(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.target_course = data
        self.lbl_target.setText(f"{data['name']}")
        self.log(f"🎯 锁定: {data['name']}")

    def toggle_grabbing(self, checked):
        if checked:
            if not self.cookies:
                QMessageBox.warning(self, "警告", "请先登录")
                self.btn_start.setChecked(False)
                return
            if not self.target_course:
                QMessageBox.warning(self, "警告", "请先选课")
                self.btn_start.setChecked(False)
                return
            
            # 显示当前选择的抢课模式
            mode_text = self.combo_type.currentText()
            self.log(f"💡 模式: {mode_text}")
            
            self.timer.start(self.spin_interval.value())
            self.btn_start.setText(f"⏹️ 停止中...")
            self.btn_start.setStyleSheet("background-color: red; color: white;")
            self.log(f"🚀 开始抢: {self.target_course['name']}")
        else:
            self.timer.stop()
            self.btn_start.setText("🚀 启动循环")
            self.btn_start.setStyleSheet("background-color: #d83b01; color: white;")
            self.log("⏹️ 已停止")

    def send_request(self):
        if not self.target_course: return

        # 🟢 获取下拉菜单里当前选择的 internal value (例如 sztzk-b-b)
        current_xkfsdm = self.combo_type.currentData()

        data = {
            'cxsfmt': '1', 'p_pylx': '1', 'mxpylx': '1',
            'p_sfgldjr': '0', 'p_sfredis': '0', 'p_sfsyxkgwc': '0',
            'p_xktjz': 'rwtjzyx', 'p_chaxunxh': '', 'p_gjz': '', 'p_skjs': '',
            'p_xn': DEFAULT_XN, 'p_xq': DEFAULT_XQ, 'p_xnxq': DEFAULT_XNXQ,
            'p_dqxn': DEFAULT_XN, 'p_dqxq': DEFAULT_XQ, 'p_dqxnxq': DEFAULT_XNXQ,
            'p_xkfsdm': current_xkfsdm,  # <--- 🟢 重点：这里使用动态变量，不再是死代码
            'p_xiaoqu': '', 'p_kkyx': '', 'p_kclb': '',
            'p_xkxs': '', 'p_dyc': '', 'p_kkxnxq': '',
            'p_id': self.target_course['pid'],
            'p_kcdm_cxrw': self.target_course['kcdm'],
            'p_kcdm_cxrw_zckc': self.target_course['kcdm'],
            'p_sfhlctkc': '0', 'p_sfhllrlkc': '0', 'p_kxsj_xqj': '',
            'p_kxsj_ksjc': '', 'p_kxsj_jsjc': '', 'p_kcdm_js': '',
            'p_kc_gjz': '', 'p_xzcxtjz_nj': '', 'p_xzcxtjz_yx': '',
            'p_xzcxtjz_zy': '', 'p_xzcxtjz_zyfx': '', 'p_xzcxtjz_bj': '',
            'p_sfxsgwckb': '1', 'p_skyy': '', 'p_sfmxzj': '0',
            'p_chaxunxkfsdm': '', 'pageNum': '1', 'pageSize': '23',
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': LOGIN_URL,
            'X-Requested-With': 'XMLHttpRequest'
        }

        try:
            r = self.sess.post(API_URL, headers=headers, data=data, cookies=self.cookies, verify=False, timeout=3)
            if "成功" in r.text or '"jg":"1"' in r.text:
                self.log(f"🎉 抢到了！{self.target_course['name']}")
                self.btn_start.click()
                QMessageBox.information(self, "成功", f"恭喜！{self.target_course['name']} 选课成功！")
            else:
                self.log(f"❌ 失败: {r.text[:40]}...")
        except Exception as e:
            self.log(f"⚠️ 网络错误: {e}")

    @Slot(object)
    def on_cookie_added(self, cookie):
        self.cookies[bytes(cookie.name()).decode()] = bytes(cookie.value()).decode()

    def log(self, text):
        self.log_box.append(text)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

if __name__ == "__main__":
    sys.argv.append("--ignore-certificate-errors")
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())
