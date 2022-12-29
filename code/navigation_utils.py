def print_to_page():
    print("Printing...")

def navigate_to_page(page):
    current_page = check_current_page()
    toggle_element_display(current_page)
    toggle_nav_active(current_page)
    toggle_element_display(page)
    toggle_nav_active(page)
    update_current_page(page)

def toggle_element_display(id):
    el = Element(id)
    if "d-none" in el.element.classList:
        el.remove_class("d-none")
    else: 
        el.add_class("d-none")

def toggle_nav_active(page):
    el = Element(page+'_button')
    if "active" in el.element.classList:
        el.remove_class("active")
    else: 
        el.add_class("active")

def check_current_page():
    el = Element('current-page')
    return str(el.element.classList)

def update_current_page(page):
    el = Element('current-page')
    el.remove_class(str(el.element.classList))
    el.add_class(page)