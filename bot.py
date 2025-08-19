import requests
import time
import os
import json
from colorama import Fore, Style, init
from typing import List, Dict, Any
import logging
import sys
import random

# 初始化colorama
init(autoreset=True)

# 美化UI常量
class UIStyle:
    # 颜色主题
    PRIMARY = Fore.CYAN + Style.BRIGHT
    SUCCESS = Fore.GREEN + Style.BRIGHT
    WARNING = Fore.YELLOW + Style.BRIGHT
    ERROR = Fore.RED + Style.BRIGHT
    INFO = Fore.BLUE + Style.BRIGHT
    HIGHLIGHT = Fore.MAGENTA + Style.BRIGHT
    MUTED = Fore.WHITE + Style.DIM
    
    # 图标
    ROCKET = "🚀"
    STAR = "⭐"
    DIAMOND = "💎"
    FIRE = "🔥"
    CROWN = "👑"
    MONEY = "💰"
    CHART = "📊"
    CHECK = "✅"
    CROSS = "❌"
    HOURGLASS = "⏳"
    SPARKLES = "✨"
    TARGET = "🎯"
    PARTY = "🎉"
    EYES = "👀"
    
    # 分隔线
    SEPARATOR = "═" * 60
    THIN_SEPARATOR = "─" * 60
    
    @staticmethod
    def gradient_text(text: str, start_color: str, end_color: str) -> str:
        """创建渐变文字效果"""
        return f"{start_color}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def box_text(text: str, color: str = Fore.CYAN) -> str:
        """创建边框文字"""
        import unicodedata
        
        def display_width(s: str) -> int:
            """计算字符串的显示宽度，考虑emoji和中文字符"""
            width = 0
            for char in s:
                if unicodedata.east_asian_width(char) in ('F', 'W'):  # 全角字符
                    width += 2
                elif ord(char) >= 0x1F000:  # emoji范围
                    width += 2
                else:
                    width += 1
            return width
        
        lines = text.split('\n')
        max_width = max(display_width(line) for line in lines)
        border = "┌" + "─" * (max_width + 2) + "┐"
        bottom = "└" + "─" * (max_width + 2) + "┘"
        
        result = [f"{color}{border}"]
        for line in lines:
            padding = max_width - display_width(line)
            result.append(f"{color}│ {line}{' ' * padding} │")
        result.append(f"{color}{bottom}{Style.RESET_ALL}")
        return '\n'.join(result)
    
    @staticmethod
    def progress_bar(current: int, total: int, width: int = 30) -> str:
        """创建进度条"""
        percentage = current / total
        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)
        return f"{UIStyle.INFO}[{bar}] {current}/{total} ({percentage:.1%}){Style.RESET_ALL}"

class EthernAirdropBot:
    """Ethern空投查询机器人"""
    
    def __init__(self):
        self.url = "https://qkrepcbzxngrtjlwjuos.supabase.co/functions/v1/blockchain-data-fetcher"
        self.headers = {
            "accept": "*/*",
            "accept-language": "zh-HK,zh-TW;q=0.9,zh;q=0.8",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrcmVwY2J6eG5ncnRqbHdqdW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzNTc5NDksImV4cCI6MjA3MDkzMzk0OX0.4N4Vo88amAAPU0wx8dgTAHkcE8krOlr8uWTOPUdjNTg",
            "content-type": "application/json",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        # 初始化日志（仅控制台输出）
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """设置日志配置"""
        # 仅配置控制台输出
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str) -> None:
        """统一日志输出"""
        print(message)
        # 移除颜色代码后记录到文件
        clean_message = message.replace(Fore.GREEN, '').replace(Fore.RED, '').replace(Fore.YELLOW, '').replace(Style.RESET_ALL, '')
        self.logger.info(clean_message)
    
    def load_accounts(self, filename: str = 'accounts.txt') -> List[str]:
        """从文件加载钱包地址"""
        accounts = []
        invalid_lines = []
        
        print(f"\n{UIStyle.INFO}{UIStyle.EYES} 正在加载地址文件: {UIStyle.HIGHLIGHT}{filename}{Style.RESET_ALL}")
        
        try:
            if not os.path.exists(filename):
                print(f"{UIStyle.ERROR}{UIStyle.CROSS} 文件 {UIStyle.HIGHLIGHT}{filename}{UIStyle.ERROR} 不存在，请创建该文件并添加钱包地址{Style.RESET_ALL}")
                return []
            
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                total_lines = len(lines)
                
                print(f"{UIStyle.INFO}{UIStyle.HOURGLASS} 发现 {UIStyle.HIGHLIGHT}{total_lines}{UIStyle.INFO} 行数据，正在验证...{Style.RESET_ALL}")
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    # 跳过空行和注释行（以#开头的行）
                    if not line or line.startswith('#'):
                        continue
                    
                    # 验证地址格式（以0x开头，42个字符）
                    if line.startswith('0x') and len(line) == 42:
                        accounts.append(line.lower())
                    else:
                        invalid_lines.append((line_num, line))
            
            # 显示加载结果
            if accounts:
                print(f"{UIStyle.SUCCESS}{UIStyle.CHECK} 成功加载 {UIStyle.HIGHLIGHT}{len(accounts)}{UIStyle.SUCCESS} 个有效地址 {UIStyle.STAR}{Style.RESET_ALL}")
            
            if invalid_lines:
                print(f"{UIStyle.WARNING}{UIStyle.CROSS} 发现 {UIStyle.HIGHLIGHT}{len(invalid_lines)}{UIStyle.WARNING} 个无效地址:")
                for line_num, invalid_addr in invalid_lines[:3]:  # 只显示前3个
                    print(f"  {UIStyle.MUTED}第{line_num}行: {invalid_addr[:20]}...{Style.RESET_ALL}")
                if len(invalid_lines) > 3:
                    print(f"  {UIStyle.MUTED}... 还有 {len(invalid_lines) - 3} 个无效地址{Style.RESET_ALL}")
            
            return accounts
            
        except Exception as e:
            print(f"{UIStyle.ERROR}{UIStyle.CROSS} 读取文件 {UIStyle.HIGHLIGHT}{filename}{UIStyle.ERROR} 时出错: {UIStyle.MUTED}{str(e)}{Style.RESET_ALL}")
            return []

    def fetch_airdrop(self, address: str) -> Dict[str, Any]:
        """查询单个钱包的空投数据"""
        try:
            payload = {"address": address}
            response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.status_code, "message": response.text}
        except Exception as e:
            return {"error": "exception", "message": str(e)}
    
    def process_batch(self, accounts: List[str], delay: float = 1.0) -> Dict[str, Any]:
        """批量处理钱包地址查询"""
        results = {}
        total = len(accounts)
        
        self.log(f"{UIStyle.SUCCESS}{UIStyle.ROCKET} 开始批量查询 {UIStyle.HIGHLIGHT}{total}{UIStyle.SUCCESS} 个钱包地址...{Style.RESET_ALL}")
        print(f"{UIStyle.MUTED}{UIStyle.THIN_SEPARATOR}{Style.RESET_ALL}")
        
        for i, addr in enumerate(accounts, 1):
            # 美化的查询进度显示
            progress_bar = UIStyle.progress_bar(i-1, total, 25)
            print(f"\n{progress_bar}")
            print(f"{UIStyle.INFO}{UIStyle.EYES} [{i}/{total}] 查询地址: {UIStyle.HIGHLIGHT}{addr[:10]}...{addr[-8:]}{Style.RESET_ALL}")
            
            data = self.fetch_airdrop(addr)
            results[addr] = data
            
            if "error" in data:
                print(f"{UIStyle.ERROR}{UIStyle.CROSS} 查询失败: {UIStyle.MUTED}{data}{Style.RESET_ALL}")
            else:
                # 显示空投分配信息
                allocation = data.get('allocation', 0)
                is_eligible = data.get('eligibility', {}).get('isEligible', False)
                
                if allocation > 0:
                    print(f"{UIStyle.SUCCESS}{UIStyle.CHECK} 查询成功 | {UIStyle.PARTY}{UIStyle.MONEY} 空投分配: {UIStyle.HIGHLIGHT}{allocation:,}{UIStyle.SUCCESS} 代币 {UIStyle.FIRE}{Style.RESET_ALL}")
                elif is_eligible:
                    print(f"{UIStyle.SUCCESS}{UIStyle.CHECK} 查询成功 | {UIStyle.WARNING}{UIStyle.HOURGLASS} 符合条件但暂无分配 {UIStyle.STAR}{Style.RESET_ALL}")
                else:
                    print(f"{UIStyle.SUCCESS}{UIStyle.CHECK} 查询成功 | {UIStyle.ERROR}{UIStyle.CROSS} 不符合空投条件{Style.RESET_ALL}")
            
            # 添加延迟防止API限流
            if i < total:  # 最后一个不需要延迟
                delay_time = 1.0  # 固定1秒间隔
                print(f"{UIStyle.MUTED}{UIStyle.HOURGLASS} 延迟 {delay_time:.1f}s...", end="", flush=True)
                
                # 简单的延迟动画
                for _ in range(int(delay_time * 2)):
                    print(".", end="", flush=True)
                    time.sleep(0.5)
                print("")
        
        print(f"\n{UIStyle.MUTED}{UIStyle.THIN_SEPARATOR}{Style.RESET_ALL}")
        return results
    

    
    def generate_summary(self, results: Dict[str, Any]) -> None:
        """生成查询结果汇总"""
        total_count = len(results)
        success_count = sum(1 for result in results.values() if "error" not in result)
        error_count = total_count - success_count
        
        # 统计空投分配
        total_allocation = 0
        eligible_count = 0
        allocated_count = 0
        
        for addr, data in results.items():
            if "error" not in data:
                allocation = data.get('allocation', 0)
                is_eligible = data.get('eligibility', {}).get('isEligible', False)
                
                if allocation > 0:
                    total_allocation += allocation
                    allocated_count += 1
                elif is_eligible:
                    eligible_count += 1
        
        # 创建超级炫酷的汇总报告
        print(f"\n\n{UIStyle.SEPARATOR}")
        
        # 标题部分
        title = f"{UIStyle.CHART} 查询结果汇总报告 {UIStyle.CHART}"
        print(UIStyle.box_text(title, UIStyle.PRIMARY))
        
        # 基础统计
        print(f"\n{UIStyle.INFO}{UIStyle.TARGET} 基础统计:")
        print(f"  {UIStyle.SUCCESS}{UIStyle.CHECK} 查询成功: {UIStyle.HIGHLIGHT}{success_count}{UIStyle.SUCCESS} 个地址")
        
        if error_count > 0:
            print(f"  {UIStyle.ERROR}{UIStyle.CROSS} 查询失败: {UIStyle.HIGHLIGHT}{error_count}{UIStyle.ERROR} 个地址")
        
        # 空投分配统计 - 超级炫酷显示
        print(f"\n{UIStyle.HIGHLIGHT}{UIStyle.FIRE} 空投分配统计:")
        
        if allocated_count > 0:
            # 获得空投的地址 - 金光闪闪效果
            airdrop_text = f"{UIStyle.PARTY} 获得空投: {UIStyle.HIGHLIGHT}{allocated_count}{UIStyle.SUCCESS} 个地址"
            token_text = f"{UIStyle.MONEY} 总计代币: {UIStyle.HIGHLIGHT}{total_allocation:,}{UIStyle.SUCCESS} 枚 {UIStyle.DIAMOND}"
            print(f"  {UIStyle.SUCCESS}{airdrop_text}")
            print(f"  {UIStyle.SUCCESS}{token_text}")
            
            # 计算平均分配
            avg_allocation = total_allocation / allocated_count
            print(f"  {UIStyle.INFO}{UIStyle.STAR} 平均分配: {UIStyle.HIGHLIGHT}{avg_allocation:,.0f}{UIStyle.INFO} 代币/地址")
        
        if eligible_count > 0:
            print(f"  {UIStyle.WARNING}{UIStyle.HOURGLASS} 符合条件但暂无分配: {UIStyle.HIGHLIGHT}{eligible_count}{UIStyle.WARNING} 个地址")
        
        ineligible_count = success_count - allocated_count - eligible_count
        if ineligible_count > 0:
            print(f"  {UIStyle.ERROR}{UIStyle.CROSS} 不符合条件: {UIStyle.HIGHLIGHT}{ineligible_count}{UIStyle.ERROR} 个地址")
        
        # 成功率统计
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        airdrop_rate = (allocated_count / total_count) * 100 if total_count > 0 else 0
        
        print(f"\n{UIStyle.INFO}{UIStyle.CHART} 统计指标:")
        print(f"  {UIStyle.SUCCESS}{UIStyle.TARGET} 查询成功率: {UIStyle.HIGHLIGHT}{success_rate:.1f}%")
        print(f"  {UIStyle.SUCCESS}{UIStyle.CROWN} 空投获得率: {UIStyle.HIGHLIGHT}{airdrop_rate:.1f}%")
        
        print(f"\n{UIStyle.SEPARATOR}")
        
        # 如果有空投，显示庆祝信息
        if total_allocation > 0:
            celebration = f"{UIStyle.PARTY} 恭喜！总共获得 {total_allocation:,} 枚代币！{UIStyle.PARTY}"
            print(UIStyle.box_text(celebration, UIStyle.SUCCESS))
        
        print()
    
    def show_welcome(self) -> None:
        """显示欢迎界面"""
        welcome_text = f"""
{UIStyle.ROCKET} ETHERN 空投查询工具 {UIStyle.ROCKET}
{UIStyle.SPARKLES} 专业级批量查询系统 {UIStyle.SPARKLES}

{UIStyle.MUTED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{UIStyle.HIGHLIGHT}✨ 功能特性:
{UIStyle.SUCCESS}  • 批量地址查询 {UIStyle.TARGET}
{UIStyle.SUCCESS}  • 实时空投分配显示 {UIStyle.MONEY}
{UIStyle.SUCCESS}  • 智能防限流机制 {UIStyle.FIRE}
{UIStyle.SUCCESS}  • 彩色进度追踪 {UIStyle.CHART}
{UIStyle.SUCCESS}  • 详细统计报告 {UIStyle.CROWN}

{UIStyle.MUTED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        print(UIStyle.box_text(welcome_text.strip(), UIStyle.PRIMARY))
        print()
    
    def run(self, accounts_file: str = 'accounts.txt', delay: float = 1.0) -> None:
        """主运行函数"""
        # 显示欢迎界面
        self.show_welcome()
        
        self.log(f"{UIStyle.SUCCESS}{UIStyle.TARGET} Ethern空投查询机器人启动")
        
        # 加载钱包地址
        accounts = self.load_accounts(accounts_file)
        if not accounts:
            self.log(f"{UIStyle.ERROR}{UIStyle.CROSS} 没有找到有效的钱包地址，程序退出{Style.RESET_ALL}")
            return
        
        self.log(f"{UIStyle.INFO}{UIStyle.EYES} 发现 {UIStyle.HIGHLIGHT}{len(accounts)}{UIStyle.INFO} 个地址待查询\n")
        
        # 批量查询
        results = self.process_batch(accounts, delay)
        
        # 结果已在内存中处理完成
        
        # 生成汇总报告
        self.generate_summary(results)
        
        self.log(f"{UIStyle.SUCCESS}{UIStyle.PARTY} 批量查询完成！{Style.RESET_ALL}")


def main():
    """程序入口点"""
    bot = EthernAirdropBot()
    bot.run()


if __name__ == "__main__":
    main()