#!/usr/bin/env python3
"""Real Chromium DOM/key test on local mock UI; not Netflix/Disney itself."""
from pathlib import Path
from playwright.sync_api import sync_playwright
base=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':900,'height':620})
    page.set_content('''<!doctype html><html><head><style>
    body{background:#12121a} button{position:absolute;width:140px;height:90px}
    #n{left:40px;top:70px}#d{left:250px;top:70px}#b{left:40px;top:230px}
    </style></head><body><button id="n" onclick="document.body.dataset.clicked='netflix'">Netflix</button>
    <button id="d" onclick="document.body.dataset.clicked='disney'">Disney+</button>
    <button id="b">Browse</button></body></html>''')
    page.add_script_tag(path=str(base/'navigation-core.js'))
    page.add_script_tag(path=str(base/'navigation.js'))
    page.keyboard.press('F9')
    assert page.locator('#n').get_attribute('data-pitv-focus-v33')=='1'
    page.keyboard.press('ArrowRight')
    assert page.locator('#d').get_attribute('data-pitv-focus-v33')=='1','right should select Disney'
    page.keyboard.press('Enter')
    assert page.locator('body').get_attribute('data-clicked')=='disney','Enter should click selected card'
    page.keyboard.press('F9')
    page.keyboard.press('ArrowDown')
    assert page.locator('#b').get_attribute('data-pitv-focus-v33')=='1','down should select Browse'
    # Verify dialog receives priority; arbitrary first main page button should be ignored.
    page.evaluate('''() => {let d=document.createElement('div');d.setAttribute('role','dialog');
      d.style.cssText='position:fixed;left:320px;top:320px;width:200px;height:180px;background:black';
      d.innerHTML='<button id="modal" style="position:relative;left:10px;top:10px;width:90px;height:45px">Confirm</button>';
      document.body.appendChild(d);}''')
    page.keyboard.press('F9')
    assert page.locator('#modal').get_attribute('data-pitv-focus-v33')=='1','modal should trap navigation'
    # Once playing full-screen, arrows must pass through to the player itself.
    page.evaluate('''() => {document.body.dataset.keypass='no';
      const video=document.createElement('video');document.body.appendChild(video);
      Object.defineProperty(document,'fullscreenElement',{configurable:true,get:()=>video});
      document.addEventListener('keydown',ev=>{if(ev.key==='ArrowRight')document.body.dataset.keypass='yes';});}''')
    page.keyboard.press('ArrowRight')
    assert page.locator('body').get_attribute('data-keypass')=='yes','video player must receive arrows'
    print('OK – headless Chromium: 6 D-pad/OK/dialog/player controls')
    browser.close()
