import os

files = [
    r'c:\Users\DELL PC\Desktop\Kurs ishi\templates\core\transaction_list.html',
    r'c:\Users\DELL PC\Desktop\Kurs ishi\templates\core\product_list.html',
    r'c:\Users\DELL PC\Desktop\Kurs ishi\templates\core\forecast.html'
]
for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace("selected_type=='in'", "selected_type == 'in'")
    content = content.replace("selected_type=='out'", "selected_type == 'out'")
    content = content.replace("selected_type=='transfer'", "selected_type == 'transfer'")
    content = content.replace("selected_warehouse_id=='wh.id'", "selected_warehouse_id == wh.id")
    content = content.replace("selected_warehouse_id==wh.id", "selected_warehouse_id == wh.id")
    content = content.replace("selected_category_id==cat.id", "selected_category_id == cat.id")
    content = content.replace("selected_product.id==p.id", "selected_product.id == p.id")

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done format fixes')
