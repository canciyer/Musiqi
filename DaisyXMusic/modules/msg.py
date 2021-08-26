# Daisyxmusic (Telegram bot project )

# Copyright (C) 2021  Bemro-Official 
# Copyright (C) 2021  Inukaasith (Modified)
# Copyright (C) 2021  Technical-Hunter (Modified)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from DaisyXMusic.config import SOURCE_CODE,ASSISTANT_NAME,PROJECT_NAME,SUPPORT_GROUP,UPDATES_CHANNEL

class Messages():
      START_MSG = """
**Salam 👋 [{}](tg://user?id={})!**

🤖 Group Muzik Bot Azərbaycanda yaradılan ilk mahnı botudur! Botu səsli söhbtdə mahnı qoşmaq üçün istifadə edə bilərsiniz.

Ətraflı məlumat üçün /help
"""
      
      HELP_MSG = [
        ".",
f"""
**Salam {PROJECT_NAME} bota xoş gəldin!
{PROJECT_NAME} Sizin qruplarda səsli söhbətdə musiqi səsləndirmək üçün yaradılmışdır!
Asistan adı: @{ASSISTANT_NAME}

Qurulum üçün növbəti menuya keçid edin**
""",

f"""
**QURULUM**

1. Botu qrupa əlavə edin
2. Qrupda bota admin yetkisi verin
3. Hər hansısa bir admin (/play) əmrini qrupa gönrərsin
4. @{ASSISTANT_NAME} qrupa daxil olmazsa /userjoin əmri ilə dəvət edin!

**ƏMRLƏR**

- /play: «Mahnı adı» Səslidə musiqi səsləndirin
- /play «yt url» : Play the given yt url
- /play «Bir mahnıya cavab verin» : Cavab verdiyiniz mahnını səsləndirir
- /player: Ayarlar menyusunu açır
- /skip: Mahnılar arasında keçid edir.
- /pause: Mahnıya fasilə verir
- /resume: Fasilə verilən mahnı davam edir
- /end: Mahnını bitirir
- /current: Hazırda səslənən müsiqini göstərir
- /playlist: Sırada olan bütün mahnıları göstərir

Botu sadəcə adminlər və admin icazəsi verilən istifadəçilər işlədə bilər.
""",
        
f"""
**Qrup adminləri üçün nəzərdə tutulub**

- /musicplayer «on/off»: Qrupda botu aktiv/deaktiv et
- /admincache: Admin list yenilə
- /userjoin: @{ASSISTANT_NAME} qrupa əlavə et
- /auth «mesaja cavab» - İstifadəçiə bot icazəsi verin
- /deauth «mesaja cavab» - İstifadəçidən icazəni alın


**Bot adminləri üçün nəzərdə tutulub**

 - /userleaveall - Userbotu bütün qruplardan atın
 - /gcast «mesaja cavab» - Bütün qruplara mesaj göndərir
 - /pmpermit «on/off» - Asistan mesajını aç/bağla
"""
      ]
