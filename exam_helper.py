import asyncio
import logging
import sys
from urllib.parse import urlparse

from playwright.async_api import Page, Response, async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_answer(answer_str: str):
    answer_str = answer_str.strip()
    answer_str = answer_str.replace('"', "").replace("'", "")
    answer_str = answer_str.replace("[", "").replace("]", "")
    answer_str = answer_str.replace("，", ",").replace("；", ";").replace("、", ",")
    answer_str = answer_str.replace(" ", "")
    if "," in answer_str:
        parts = answer_str.split(",")
    elif ";" in answer_str:
        parts = answer_str.split(";")
    else:
        parts = [answer_str]
    answers = []
    for part in parts:
        part = part.strip().upper()
        if not part:
            continue
        if len(part) > 1 and part.isalpha() and all(ch.isalpha() for ch in part):
            answers.extend(list(part))
        else:
            answers.append(part)
    return answers


async def normalize_text(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum()).lower()


async def find_question_block(page: Page, question_content: str):
    selectors = [".problem", ".question-item", ".question", ".exam-question", ".question-block"]
    target = await normalize_text(question_content)
    if not target:
        return None

    for sel in selectors:
        blocks = await page.query_selector_all(sel)
        for block in blocks:
            text = await block.inner_text()
            norm_text = await normalize_text(text)
            if target in norm_text or norm_text in target:
                return block
    return None


async def click_answer(elem, answer: str):
    answer = answer.strip().upper()
    selectors = [
        f"input[type='radio'][value='{answer}']",
        f"input[type='checkbox'][value='{answer}']",
        f"input[value='{answer}']",
    ]
    for selector in selectors:
        element = await elem.query_selector(selector)
        if element:
            await element.click()
            return True
    label = await elem.query_selector(f"label:has-text('{answer}')")
    if label:
        await label.click()
        return True
    return False


async def fill_answers(page: Page, questions):
    logger.info("Filling answers on page: %s", page.url)
    for question in questions:
        block = await find_question_block(page, question["content"])
        if not block:
            logger.info("No block found for question: %s", question["content"][:50])
            continue

        for answer in question["answers"]:
            if await click_answer(block, answer):
                logger.info("Clicked answer %s", answer)
            else:
                logger.info("Could not click answer %s for question", answer)


async def main(url: str):
    questions = []
    question_event = asyncio.Event()

    async def intercept_start_exam(response: Response):
        if "startExam" in response.url or "selectExamInfo" in response.url:
            data = await response.json()
            for q in data.get("data", {}).get("paperQuesList", []):
                questions.append({
                    "content": q.get("questionContent", "").strip(),
                    "answers": parse_answer(q.get("correctAnswer", "")),
                })
            if questions and not question_event.is_set():
                question_event.set()
                logger.info("Parsed %d questions from %s", len(questions), response.url)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()

    async def on_new_page(new_page: Page):
        new_page.on("response", intercept_start_exam)

    context.on("page", on_new_page)

    page = await context.new_page()
    page.on("response", intercept_start_exam)
    await page.goto(url, wait_until="domcontentloaded", timeout=120000)
    await page.wait_for_url("**/goExamNew*", timeout=120000)

    await question_event.wait()

    await asyncio.sleep(2)
    pages = context.pages
    for p in pages:
        await fill_answers(p, questions)

    logger.info("All answers attempted. Browser will remain open for review.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python exam_helper_v2.py <exam_url>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
