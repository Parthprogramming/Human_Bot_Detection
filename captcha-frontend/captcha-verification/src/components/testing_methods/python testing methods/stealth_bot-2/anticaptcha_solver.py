from anticaptchaofficial.recaptchav2proxyless import *

def solve_recaptcha(website_url, site_key):
    solver = recaptchaV2Proxyless()
    solver.set_key("YOUR_ANTI_CAPTCHA_KEY")
    solver.set_website_url(website_url)
    solver.set_website_key(site_key)
    g_response = solver.solve_and_return_solution()
    if g_response:
        print("✅ Captcha Solved:", g_response)
        return g_response
    else:
        print("❌ Captcha failed:", solver.error_code)
