Задача: Мобильные приложения содержат необходимые для своей работы ресурсы, в частности, строки. Поскольку приложение может работать с несколькими языками, существуют и локализированные строки. Текст в них может быть фиксированным, но может и содержать динамически подставляемые значения, например:
- Привет, %1$s! (Android)
- Привет, :name! (iOS)

При переводах такие форматированные строки могут быть испорчены. Кроме того, строки могут содержать CDATA, который тоже может некорректно перевестись.
Задача проверки строк была решена скриптом в этом репозитории.
При запуске необходимо указать ОС и путь к корневому каталогу строковых ресурсов.
В данном случае за основу взяты английские строки, с которыми и сравниваются локализированные.
На выходе получится файл с указанием поврежденных строк и ключей:
```
This key is missing in the translation!
path = C:/Users/VladEremeev/AndroidStudioProjects/.../app/src/main/res/values-ar/strings.xml
key= error.input.android 

Wrong number of tags in CDATA!
path = C:/Users/VladEremeev/AndroidStudioProjects/.../app/src/main/res/values-cs/strings.xml
key= authorization.signUp.privacyPolicyAgreement.android
Expected result: ['<b>', '<font color="#0984E3">', '</font>', '</b>'] ; 
 Actual =  ['<font color="#0984E3">', '</font>'] 
 
Wrong number of resource arguments in string!
(some example)
```
