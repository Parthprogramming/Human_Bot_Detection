# bot_playwright_v2.py  ⟶  works with playwright-stealth 2.x
import asyncio, random, math
from playwright.async_api import async_playwright
from playwright_stealth import Stealth           # NEW API

USAI = "jupiter5002"

async def main():
    # “Recommended usage” — every page created inside the block is stealthy
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=False,
                                          args=['--start-maximized'])
        page = await browser.new_page(viewport={'width':1280,'height':900})

        await page.goto("http://localhost:3000/")

        # smooth scroll with variable speed and pauses
        for y in range(0, 600, random.randint(40, 80)):  # Variable scroll steps
            await page.evaluate("y=>window.scrollTo(0,y)", y)
            await page.wait_for_timeout(random.randint(50, 220))

        # Wait for input field using placeholder
        input_field = await page.wait_for_selector("input[placeholder='Enter USAI ID']", 
                                                 state="visible")
        
        # Get input field position for natural mouse movement
        input_box = await input_field.bounding_box()
        
        # Move mouse in a natural curve to input field
        await page.mouse.move(
            input_box['x'] + input_box['width'] / 2 + random.uniform(-10, 10),
            input_box['y'] + input_box['height'] / 2 + random.uniform(-5, 5),
            steps=random.randint(10, 20)  # Random number of steps for natural movement
        )
        
        # Small pause before clicking
        await page.wait_for_timeout(random.randint(100, 300))
        
        # Click with slight offset
        await page.mouse.click(
            input_box['x'] + input_box['width'] / 2 + random.uniform(-3, 3),
            input_box['y'] + input_box['height'] / 2 + random.uniform(-2, 2)
        )

        # Type with variable delays and occasional pauses
        for ch in USAI:
            await page.keyboard.type(ch, delay=random.randint(80, 200))
            if random.random() < 0.1:  # 10% chance of longer pause
                await page.wait_for_timeout(random.randint(200, 400))
        
        # Wait for and find submit button by text content
        verify_button = await page.wait_for_selector("button:has-text('Verify')", 
                                                   state="visible")
        button_box = await verify_button.bounding_box()
        
        # Move to button with natural curve
        await page.mouse.move(
            button_box['x'] + button_box['width'] / 2 + random.uniform(-8, 8),
            button_box['y'] + button_box['height'] / 2 + random.uniform(-4, 4),
            steps=random.randint(8, 15)
        )
        
        # Hover pause
        await page.wait_for_timeout(random.randint(150, 300))
        
        # Click button with slight offset
        await page.mouse.click(
            button_box['x'] + button_box['width'] / 2 + random.uniform(-2, 2),
            button_box['y'] + button_box['height'] / 2 + random.uniform(-2, 2)
        )

        # Variable wait time after submission
        await page.wait_for_timeout(random.randint(3000, 5000))
        await browser.close()

asyncio.run(main())


# ------------------------------------------

# bot_playwright_v2.py  ⟶  works with playwright-stealth 2.x
# import asyncio, random, math
# from playwright.async_api import async_playwright
# from playwright_stealth import Stealth           # NEW API

# USAI = "jupiter5002"

# async def main():
#     # “Recommended usage” — every page created inside the block is stealthy
#     async with Stealth().use_async(async_playwright()) as p:
#         browser = await p.chromium.launch(headless=False,
#                                           args=['--start-maximized'])
#         page = await browser.new_page(viewport={'width':1280,'height':900})

#         await page.goto("http://localhost:3000/")

#         # smooth scroll
#         for y in range(0, 600, 60):
#             await page.evaluate("y=>window.scrollTo(0,y)", y)
#             await page.wait_for_timeout(random.randint(50, 220))

#         # focus & type
#         await page.click("#inputfield", delay=120)
#         for ch in USAI:
#             await page.keyboard.type(ch, delay=random.randint(80, 200))
            
#         await page.click('#tosubmitform', delay=140)
#         # await page.click("#tosubmitform", delay=140)
#         await page.wait_for_timeout(4000)
#         await browser.close()

# asyncio.run(main())
