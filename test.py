import argostranslate.package
import argostranslate.translate

# Install translation packages (only need to do this once)
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(
    filter(
        lambda x: x.from_code == "ru" and x.to_code == "en", available_packages
    )
)
argostranslate.package.install_from_path(package_to_install.download())

text ="""
Главные новости 26 февраля

✹ Трамп заявил что Зеленский 28 февраля приедет в Вашингтон. В ходе визита подпишут соглашение по природным ресурсам. Президент Украины сказал, что в тексте «нет всех гарантий безопасности, которые хотела видеть Украина, но есть хотя бы предложение».

✹ «Украине следует забыть о НАТО. Путин очень хитрый парень». Дональд Трамп выступил на первом заседании кабинета министров США. Здесь  можно прочитать краткий пересказ.

✹ Politico : в Госдепартаменте составляют список исключений из приостановки помощи для Украины.

✹ Кинокритика Екатерину Барабаш отправили под домашний арест  по делу о «фейках» про армию.

✹ Трамп предложил продавать за пять миллионов долларов «золотые карты», дающие право претендовать на гражданство США.

✹ В Румынии задержали Кэлина Джеорджеску — победителя аннулированного первого тура выборов президента.

———

Текст дня (https://bit.ly/meduzamirror#/feature/2025/02/26/irina-viner-20-let-byla-samoy-vliyatelnoy-figuroy-v-hudozhestvennoy-gimnastike-ee-kariera-vnezapno-oborvalas-iz-za-konflikta-s-vliyatelnoy-uchenitsey-alinoy-kabaevoy): Ирина Винер 20 лет была самой влиятельной фигурой в художественной гимнастике. Ее карьера внезапно оборвалась из-за конфликта с влиятельной ученицей — Алиной Кабаевой. «Медуза» подводит итоги «эпохи Винер».
"""
# Translate text
translated_text = argostranslate.translate.translate(text, "ru", "en")
print(translated_text)  # Output: ¡Hola, mundo!