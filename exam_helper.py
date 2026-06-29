import asyncio
import json
import logging
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright, Page, Response
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exam_helper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExamHelper:
    def __init__(self):
        self.exam_params: Dict[str, Any] = {}
        self.questions: List[Dict[str, Any]] = []
        self.start_exam_response: Optional[Dict[str, Any]] = None
        self.url_params: Dict[str, str] = {}

    def parse_url_params(self, url: str) -> Dict[str, str]:
        """从 URL 中解析参数"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        result = {}
        for key, value in params.items():
            result[key] = value[0] if isinstance(value, list) and len(value) > 0 else value
        logger.info(f"解析 URL 参数: {result}")
        return result

    async def wait_for_login(self, page: Page) -> bool:
        """等待用户登录"""
        logger.info("Please complete login manually...")
        try:
            await page.wait_for_url("**/goExamNew*", timeout=3000000000)
            logger.info("Detected exam page entry")
            return True
        except Exception as e:
            logger.error(f"Login timeout or page redirect failed: {e}")
            return False

    async def intercept_start_exam(self, response: Response):
        """拦截考试相关接口"""
        # 匹配 startExam 接口
        if "startExam" in response.url or "start_exam" in response.url or "/api/exam/startExam" in response.url:
            logger.info(f"Captured startExam request: {response.url}")
            try:
                self.start_exam_response = await response.json()
                logger.info(f"startExam response data obtained")
                self.parse_exam_params()
                self.parse_questions()
            except Exception as e:
                logger.error(f"Failed to parse startExam response: {e}")
        
        # 同时监听 selectExamInfo 接口获取基本信息
        if "selectExamInfo" in response.url:
            logger.info(f"Captured selectExamInfo request: {response.url}")
            try:
                data = await response.json()
                # 保存基本信息
                if not self.start_exam_response:
                    self.start_exam_response = data
                    self.parse_exam_params()
            except Exception as e:
                logger.error(f"Failed to parse selectExamInfo response: {e}")

    def parse_exam_params(self):
        """从响应中提取考试参数"""
        if not self.start_exam_response:
            return
        
        data = self.start_exam_response.get('data', {})
        
        # 尝试从 startExam 格式解析
        if data.get('examId'):
            self.exam_params['examId'] = data.get('examId')
            self.exam_params['archivesId'] = data.get('archivesId')
            self.exam_params['paperId'] = data.get('paperId')
        # 尝试从 selectExamInfo 格式解析
        elif data.get('customExam'):
            custom_exam = data.get('customExam', {})
            self.exam_params['examId'] = custom_exam.get('examId')
            self.exam_params['paperId'] = custom_exam.get('paperId')
            # archivesId 从 URL 参数获取
            if not self.exam_params.get('archivesId'):
                self.exam_params['archivesId'] = self.url_params.get('archivesId')
        
        logger.info(f"Exam params extracted: {self.exam_params}")

    def parse_questions(self):
        """解析题目列表"""
        if not self.start_exam_response:
            return
        
        data = self.start_exam_response.get('data', {})
        paper_ques_list = data.get('paperQuesList', [])
        
        for question in paper_ques_list:
            question_id = question.get('questionId')
            question_content = question.get('questionContent', '').strip()
            correct_answer = question.get('correctAnswer', '')
            
            answer_list = self.parse_answer(correct_answer)
            
            self.questions.append({
                'questionId': question_id,
                'questionContent': question_content,
                'correctAnswer': answer_list
            })
        
        logger.info(f"共解析到 {len(self.questions)} 道题目")

    def parse_answer(self, answer_str: str) -> List[str]:
        """解析答案字符串为列表"""
        answer_str = answer_str.strip()
        if not answer_str:
            return []
        
        # 移除外层的方括号
        if answer_str.startswith('[') and answer_str.endswith(']'):
            answer_str = answer_str[1:-1].strip()
        
        # 处理多种分隔符：逗号、分号、空格
        if ',' in answer_str:
            answers = [a.strip() for a in answer_str.split(',') if a.strip()]
        elif ';' in answer_str:
            answers = [a.strip() for a in answer_str.split(';') if a.strip()]
        else:
            answers = [answer_str] if answer_str else []
        
        # 清理每个答案：移除可能残留的方括号和引号
        cleaned_answers = []
        for a in answers:
            a = a.strip()
            a = a.replace('[', '').replace(']', '')
            a = a.replace('"', '').replace("'", '')
            a = a.strip()
            if a:
                cleaned_answers.append(a.upper())
        
        return cleaned_answers

    async def fill_answers(self, page: Page):
        """自动填写答案 - 遍历页面问题并匹配答案"""
        if not self.questions:
            logger.warning("No questions to fill")
            return
        
        logger.info(f"Total {len(self.questions)} questions from API")
        
        # 获取页面上所有问题元素
        problem_elements = await page.query_selector_all(".problem")
        logger.info(f"Found {len(problem_elements)} problem elements on page")
        
        for idx, problem_el in enumerate(problem_elements):
            try:
                # 获取题目标题
                title_el = await problem_el.query_selector(".item-title span")
                if not title_el:
                    logger.warning(f"Question {idx + 1}: No title element found")
                    continue
                
                title_text = await title_el.inner_text()
                # 清理标题文本：移除题号和分数
                title_text = title_text.strip()
                
                # 移除开头的数字和点，如 "1." "2." "18." 等
                if title_text and title_text[0].isdigit():
                    dot_idx = title_text.find('.')
                    if dot_idx > 0:
                        title_text = title_text[dot_idx + 1:].strip()
                
                # 移除换行符（多选题标题可能有换行）
                title_text = title_text.replace('\n', ' ').replace('\r', ' ')
                
                # 移除末尾的分数，如 "（5分）"
                score_idx = title_text.find('（')
                if score_idx > 0:
                    title_text = title_text[:score_idx].strip()
                
                logger.info(f"Question {idx + 1}: {title_text[:50]}...")
                
                # 在 API 返回的题目中查找匹配
                matched_question = None
                for q in self.questions:
                    q_content = q['questionContent'].strip()
                    # 使用部分匹配（标题可能被截断）
                    if title_text in q_content or q_content in title_text:
                        matched_question = q
                        break
                    # 也尝试匹配前30个字符
                    if len(title_text) > 10 and title_text[:30] in q_content:
                        matched_question = q
                        break
                    # 尝试去除空格后匹配
                    if title_text.replace(' ', '') in q_content.replace(' ', ''):
                        matched_question = q
                        break
                
                if not matched_question:
                    logger.warning(f"Question {idx + 1}: No matching answer found")
                    continue
                
                answers = matched_question['correctAnswer']
                logger.info(f"Question {idx + 1} answer: {answers}")
                
                # 点击选项
                for answer in answers:
                    answer = answer.strip().upper()
                    
                    # 在当前问题元素内查找选项
                    option_input = await problem_el.query_selector(f"input[type='radio'][value='{answer}']")
                    if not option_input:
                        option_input = await problem_el.query_selector(f"input[type='checkbox'][value='{answer}']")
                    
                    if option_input:
                        await option_input.click()
                        await asyncio.sleep(0.2)
                    else:
                        logger.warning(f"Option {answer} not found in question {idx + 1}")
                
            except Exception as e:
                logger.error(f"Error filling question {idx + 1}: {e}")
                continue
        
        logger.info("Answers filled. Please review manually before submitting.")

    async def fill_single_question(self, page: Page, question: Dict[str, Any], index: int):
        """填写单道题目"""
        answers = question['correctAnswer']
        
        for answer in answers:
            answer = answer.strip().upper()
            
            try:
                radio_selector = f"input[type='radio'][value='{answer}']"
                checkbox_selector = f"input[type='checkbox'][value='{answer}']"
                
                try:
                    element = await page.wait_for_selector(radio_selector, timeout=3000000000)
                    await element.click()
                except:
                    try:
                        element = await page.wait_for_selector(checkbox_selector, timeout=3000000000)
                        await element.click()
                    except:
                        logger.warning(f"Element not found for option {answer}")
                        await self.scroll_to_question(page, index)
                        
                        try:
                            element = await page.wait_for_selector(radio_selector, timeout=3000000000)
                            await element.click()
                        except:
                            try:
                                element = await page.wait_for_selector(checkbox_selector, timeout=3000000000)
                                await element.click()
                            except:
                                logger.error(f"Option {answer} not found after scroll")
                                
            except Exception as e:
                logger.error(f"Error processing option {answer}: {e}")

    async def scroll_to_question(self, page: Page, index: int):
        """滚动到指定题目"""
        try:
            question_selector = f".question-item:nth-child({index})"
            element = await page.wait_for_selector(question_selector, timeout=3000000000)
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.warning(f"Failed to scroll to question {index}: {e}")
            await page.evaluate("window.scrollBy(0, 50000)")

    async def run(self):
        """主运行函数"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 用于存储新打开的 testPage 标签页
            test_page = None
            
            async def handle_new_page(new_page):
                """处理新打开的标签页"""
                nonlocal test_page
                if "testPage" in new_page.url:
                    logger.info(f"Detected testPage tab: {new_page.url}")
                    test_page = new_page
                    # 在新页面上设置响应监听
                    new_page.on("response", self.intercept_start_exam)
            
            # 监听新标签页打开事件
            context.on("page", handle_new_page)
            
            print("Please enter exam URL: ", end="", flush=True)
            url = input().strip()
            if not url:
                logger.error("URL cannot be empty")
                await browser.close()
                return
            
            self.url_params = self.parse_url_params(url)
            
            page.on("response", self.intercept_start_exam)
            
            await page.goto(url)
            
            logged_in = await self.wait_for_login(page)
            if not logged_in:
                logger.error("Login timeout")
                await browser.close()
                return
            
            logger.info("Waiting for exam basic info...")
            
            # 等待基本信息
            wait_count = 0
            while not self.start_exam_response and wait_count < 3000000000:
                await page.wait_for_timeout(3000000000)
                wait_count += 1
            
            if self.exam_params:
                logger.info(f"Exam basic info obtained: {self.exam_params}")
                logger.info("Please click 'Start Exam' button to open test page...")
            
            # 等待新标签页打开
            logger.info("Waiting for testPage tab to open...")
            wait_count = 0
            while not test_page and wait_count < 3000000000:  # 最多等待5分钟
                await page.wait_for_timeout(3000000000)
                wait_count += 1
                if wait_count % 10 == 0:
                    logger.info(f"Waiting for testPage... ({wait_count}s)")
            
            if not test_page:
                logger.error("Failed to detect testPage tab. Please click 'Start Exam' button.")
                # 继续等待
                while not test_page:
                    await page.wait_for_timeout(3000000000)
            
            logger.info(f"testPage tab detected: {test_page.url}")
            
            # 在 testPage 页面等待 startExam 接口
            logger.info("Waiting for startExam API on testPage...")
            wait_count = 0
            while not self.questions and wait_count < 120:  # 最多等待10分钟
                await page.wait_for_timeout(3000000000)
                wait_count += 1
                if wait_count % 6 == 0:
                    logger.info(f"Waiting for questions... ({wait_count * 5}s)")
            
            if not self.questions:
                logger.error("Failed to get questions from startExam API.")
                logger.info("Continuing to wait... Press Ctrl+C to exit if needed.")
                while not self.questions:
                    await page.wait_for_timeout(3000000000)
            
            if not self.questions:
                logger.error("Failed to parse questions. Please check if startExam API was called.")
                await browser.close()
                return
            
            await self.fill_answers(test_page)
            
            print("Press Enter to exit...")
            input()
            await browser.close()

if __name__ == "__main__":
    helper = ExamHelper()
    try:
        asyncio.run(helper.run())
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)