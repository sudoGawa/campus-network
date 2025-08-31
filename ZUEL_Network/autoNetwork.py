import platform
import time
import pywifi
from pywifi import const
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException,
                                        NoSuchElementException,
                                        ElementClickInterceptedException,
                                        WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
import os
import sys

# 配置信息 - 请根据实际情况修改以下参数
RETRY_COUNT = 3  # 连接失败重试次数
WAIT_TIMEOUT = 20  # 网页等待超时时间(秒)

class CampusNetworkAutoConnector:

    def __init__(self):
        self.wifi = pywifi.PyWiFi()
        self.browser = "edge"  # 根据自己的浏览器可以改为 "chrome"
        self.iface = self.wifi.interfaces()[0]  # 获取第一个无线网卡接口
        # self.file_path = '校园网.txt'
        self.file_path = self._get_config_file_path()

    def _get_config_file_path(self):
        """获取配置文件的绝对路径"""
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe文件
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是python脚本
            base_path = os.path.dirname(os.path.abspath(__file__))

        config_file = os.path.join(base_path, '校园网配置文件.txt')
        print(f"配置文件路径: {config_file}")
        return config_file

    def config_msg(self, file_path):
        """
        提取TXT文件中冒号（：）后的文本
        """
        results = {
            'WIFI_NAME': [], 'STUDENT_ID': '', 'PASSWORD': '', 'LOGIN_URL': ''
        }
        try:
            with open(file_path, 'r', encoding='utf-8') as file:

                for i, line in enumerate(file):
                    value = line.split('：', 1)[1].strip()
                    # 第一行找WiFi名称
                    if i == 0:
                        # ZUEL寝室和教室的校园网WiFi的名称不一样
                        # 一定注意是中文逗号'，' 还是英文逗号',' 和配置文件.txt都采用中文逗号!
                        if '，' in value:
                            value_WiFi_1 = value.split('，',1)[0].strip()
                            results['WIFI_NAME'].append(value_WiFi_1)

                            value_WiFi_2 = value.split('，', 1)[1].strip()
                            results['WIFI_NAME'].append(value_WiFi_2)

                        else:
                            results['WIFI_NAME'].append(value)
                    # 第二行找学生号
                    elif i == 1:
                        results['STUDENT_ID'] = value
                    # 第三行找密码
                    elif i == 2:
                        results['PASSWORD'] = value
                    # 第四行找链接
                    else:
                        results['LOGIN_URL'] = value
                    # # 额外检查英文冒号（可选）
                    # elif ':' in line:
                    #     value = line.split(':', 1)[1].strip()
                    #     results.append(value)

        except Exception as e:
            print(f"处理文件时出错: {e}")
        return results

    def connect_wifi(self, ssid, retry=RETRY_COUNT):
        """连接指定WiFi"""
        print(f"尝试寻找校园网: {ssid}")

        # 断开当前所有连接
        self.iface.disconnect()
        time.sleep(2)  # 等待断开连接

        if self.iface.status() == const.IFACE_DISCONNECTED:
            # 创建WiFi连接文件
            profile = pywifi.Profile()
            profile.ssid = ssid  # WiFi名称
            profile.auth = const.AUTH_ALG_OPEN  # 开放认证
            profile.akm.append(const.AKM_TYPE_NONE)  # 无密码 (校园网通常无需密码连接后网页认证)
            profile.cipher = const.CIPHER_TYPE_CCMP

            # 删除已保存的同名WiFi配置
            self.iface.remove_all_network_profiles()
            # 添加新的WiFi配置
            tmp_profile = self.iface.add_network_profile(profile)

            # 连接WiFi
            self.iface.connect(tmp_profile)
            time.sleep(5)  # 等待连接

            # 检查连接状态
            if self.iface.status() == const.IFACE_CONNECTED:
                print(f"已找到校园网: {ssid}")
                return True
            else:
                print(f"尝试寻找校园网 {ssid} 失败")
                if retry > 0:
                    print(f"剩余重试次数: {retry - 1}")
                    return self.connect_wifi(ssid, retry - 1)
                return False
        else:
            print("当前已有校园网连接")
            return True

    def _init_browser(self):
        """初始化浏览器 - 避免联网下载驱动"""
        print(f"正在初始化{self.browser}浏览器...")

        try:
            if self.browser == "edge":
                options = webdriver.EdgeOptions()
                # 基本配置，避免复杂设置
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                # 不使用无头模式，方便观察

                # 尝试使用系统PATH中的驱动，避免联网下载
                try:
                    return webdriver.Edge(options=options)
                except Exception as e1:
                    print(f"使用系统Edge驱动失败: {str(e1)}")
                    # 尝试指定本地驱动路径
                    local_driver_paths = [
                        "./msedgedriver.exe",
                        "msedgedriver.exe",
                        "./drivers/msedgedriver.exe",
                        "C:/msedgedriver/msedgedriver.exe"
                    ]

                    for driver_path in local_driver_paths:
                        if os.path.exists(driver_path):
                            print(f"找到本地Edge驱动: {driver_path}")
                            service = EdgeService(driver_path)
                            return webdriver.Edge(service=service, options=options)

                    # 如果都失败，尝试Chrome
                    print("Edge初始化失败，尝试切换到Chrome...")
                    self.browser = "chrome"
                    return self._init_browser()

            else:  # chrome
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")

                # 尝试使用系统PATH中的驱动
                try:
                    return webdriver.Chrome(options=options)
                except Exception as e2:
                    print(f"使用系统Chrome驱动失败: {str(e2)}")
                    # 尝试指定本地驱动路径
                    local_driver_paths = [
                        "./chromedriver.exe",
                        "chromedriver.exe",
                        "./drivers/chromedriver.exe",
                        "C:/chromedriver/chromedriver.exe"
                    ]

                    for driver_path in local_driver_paths:
                        if os.path.exists(driver_path):
                            print(f"找到本地Chrome驱动: {driver_path}")
                            service = ChromeService(driver_path)
                            return webdriver.Chrome(service=service, options=options)

                    # 如果都失败，抛出异常
                    raise Exception("无法找到可用的浏览器驱动")

        except Exception as e:
            print(f"浏览器初始化失败: {str(e)}")
            print("解决方案：")
            print("1. 手动下载浏览器驱动文件")
            print("2. Edge驱动下载: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
            print("3. Chrome驱动下载: https://googlechromelabs.github.io/chrome-for-testing/")
            print("4. 将驱动文件放在脚本同目录下")
            raise

    def login_network(self, url, username, password):
        """通过网页登录校园网 - 重点优化异常处理"""
        print("开始登录...")

        driver = None
        try:
            # 初始化浏览器 - 这里可能会抛出异常
            try:
                driver = self._init_browser()
                print("浏览器启动成功")
            except Exception as browser_error:
                print(f"浏览器初始化失败: {str(browser_error)}")
                print("请确保：")
                print("1. 已安装Edge或Chrome浏览器")
                print("2. 浏览器驱动在系统PATH中或当前目录下")
                print("3. 网络连接正常（如需下载驱动）")
                return False

            # 执行反检测脚本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # 打开登录页面
            print(f"正在打开登录页面: {url}")
            driver.get(url)
            print("登录页面加载完成")

            # 等待页面完全加载
            time.sleep(3)

            # 调试：打印页面标题确认页面加载正确
            print(f"您的大学是: {driver.title}")

            try:
                # 等待用户名输入框出现
                username_field = WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )

                # 清空并输入用户名
                username_field.clear()
                username_field.send_keys(username)
                print(f"输入用户名: {username}")

                # 等待密码输入框
                password_field = WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )

                # 清空并输入密码
                password_field.clear()
                password_field.send_keys(password)
                print("输入密码完成")

                # 等待输入完成
                time.sleep(2)

                # 寻找登录按钮 - 这是关键部分
                print("寻找登录按钮中...")

                # 尝试多种方式找到登录按钮
                login_button = None
                button_selectors = [
                    (By.ID, "login-account"),
                    (By.CLASS_NAME, "btn-login"),
                    (By.XPATH, "//button[contains(text(), '登录')]"),
                    (By.XPATH, "//button[@type='button' and contains(@class, 'btn-login')]"),
                    (By.CSS_SELECTOR, "button.btn-login"),
                    (By.CSS_SELECTOR, "#login-account")
                ]

                for selector_type, selector_value in button_selectors:
                    try:
                        login_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        print(f"已通过 {selector_type}='{selector_value}' 找到登录按钮")
                        break
                    except TimeoutException:
                        continue

                if not login_button:
                    print("无法找到登录按钮！")
                    # 打印页面源码的按钮部分用于调试
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    print(f"页面上找到 {len(buttons)} 个按钮:")
                    for i, btn in enumerate(buttons):
                        try:
                            print(
                                f"按钮 {i + 1}: id='{btn.get_attribute('id')}', class='{btn.get_attribute('class')}', text='{btn.text}'")
                        except:
                            print(f"按钮 {i + 1}: 无法获取属性")
                    return False

                print("点击登录按钮！")

                # 确保按钮在视窗中
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
                time.sleep(1)

                # 尝试多种点击方法
                click_success = False

                # 方法1: 标准点击
                try:
                    login_button.click()
                    print("方法1: 点击成功")
                    click_success = True
                except Exception as e:
                    print(f"方法1失败: {str(e)}")

                # 方法2: JavaScript点击
                if not click_success:
                    try:
                        driver.execute_script("arguments[0].click();", login_button)
                        print("方法2: JavaScript点击成功")
                        click_success = True
                    except Exception as e:
                        print(f"方法2失败: {str(e)}")

                # 方法3: ActionChains点击
                if not click_success:
                    try:
                        ActionChains(driver).move_to_element(login_button).click().perform()
                        print("方法3: ActionChains点击成功")
                        click_success = True
                    except Exception as e:
                        print(f"方法3失败: {str(e)}")

                # 方法4: 强制JavaScript提交
                if not click_success:
                    try:
                        driver.execute_script("""
                            document.getElementById('login-account').click();
                        """)
                        print("方法4: 强制JavaScript点击成功")
                        click_success = True
                    except Exception as e:
                        print(f"方法4失败: {str(e)}")

                if not click_success:
                    print("所有点击方法都失败了！")
                    return False

                time.sleep(5)  # 等待登录处理

                # 检查登录结果
                current_url = driver.current_url
                print(f"当前URL: {current_url}")
                # 成功指示符
                success_keywords = [
                    "success", "成功", "successful", "welcome", "欢迎",
                    "已连接", "认证成功", "登录成功", "connected"
                ]
                # 1.通过检测url中是否有以上success等这些字样来判断登录是否成功！
                # 2.通过检测URL是否跳转来判断！（通常登录成功后会跳转）
                url_changed = current_url != url

                try:
                    has_success = any(keyword.lower() in current_url for keyword in success_keywords)
                    if has_success or url_changed:
                        print("登录成功！")
                        return True
                    else:
                        print("登录有可能失败！！！")

                # # 获取页面内容检查登录状态
                # try:
                #     page_source = driver.page_source
                #
                #     # 成功指示符
                #     success_keywords = [
                #         "success", "成功", "successful", "welcome", "欢迎",
                #         "已连接", "认证成功", "登录成功", "connected"
                #     ]
                #
                #     # 失败指示符
                #     error_keywords = [
                #         "error", "错误", "failed", "failure", "invalid",
                #         "incorrect", "wrong", "denied", "用户名或密码错误"
                #     ]
                #
                #     page_text_lower = page_source.lower()
                #
                #     # 检查是否有成功标识
                #     has_success = any(keyword.lower() in page_text_lower for keyword in success_keywords)
                #     # 检查是否有错误标识
                #     has_error = any(keyword.lower() in page_text_lower for keyword in error_keywords)
                #
                #     # 检查URL是否跳转（通常登录成功后会跳转）
                #     url_changed = current_url != url
                #
                #     print(f"检查结果 - 成功标识: {has_success}, 错误标识: {has_error}, URL变化: {url_changed}")
                #
                #     if has_success or (url_changed and not has_error):
                #         print("登录成功！")
                #         return True
                #     elif has_error:
                #         print("登录失败：检测到错误信息")
                #         return False
                #     else:
                #         print("登录状态不明确，建议手动检查")
                #         # 保存截图
                #         try:
                #             driver.save_screenshot("login_status_unknown.png")
                #             print("已保存截图到 login_status_unknown.png")
                #         except:
                #             pass
                #         return False

                except Exception as e:
                    print(f"检查登录状态时出错: {str(e)}")
                    return False

            # except TimeoutException:
            #     print("等待页面元素超时")
            #     return False
            except Exception as e:
                print(f"登录过程中发生错误: {str(e)}")
                return False

        except Exception as e:
            print(f"浏览器操作失败: {str(e)}")
            return False
        finally:
            # 保持浏览器开启一段时间以完成登录
            if driver:
                print("浏览器将在5秒后自动关闭")
                time.sleep(5)
                driver.quit()

    def run(self):
        """执行完整连接流程"""
        print("===== 校园网自动连接程序启动 =====")
        msg = self.config_msg(self.file_path)

        WIFI_NAME = msg['WIFI_NAME']
        STUDENT_ID = msg['STUDENT_ID']
        PASSWORD = msg['PASSWORD']
        LOGIN_URL = msg['LOGIN_URL']

        # 第一步：连接WiFi
        if self.connect_wifi(WIFI_NAME[0]):
            print(f"已找到{WIFI_NAME[0]}")
        elif self.connect_wifi(WIFI_NAME[1]):
            print(f"已找到{WIFI_NAME[1]}")
        else:
            return False

        # 等待网络就绪
        print("等待网络稳定...")
        time.sleep(5)

        # 第二步：网页登录
        if self.login_network(LOGIN_URL, STUDENT_ID, PASSWORD):

            print(f"校园网：{WIFI_NAME}已启动，请开始冲浪吧！")
            return True
        else:
            print("校园网登录失败")
            print("请检查：")
            print("1. 账号密码是否正确")
            print("2. 网络连接是否正常")
            print("3. 校园网页面是否有变化")
            return False


if __name__ == "__main__":

    connector = CampusNetworkAutoConnector()

    try:
        connector.run()
    except KeyboardInterrupt:
        print("\n 程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        print("\n 故障排除建议：")
        print("1. 确认Edge浏览器已正确安装")
        print("2. 检查网络连接状态")
        print("3. 验证账号密码正确性")
        print("4. 尝试手动登录验证页面正常")