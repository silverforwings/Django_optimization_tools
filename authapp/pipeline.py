import hashlib
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urlunparse, urlencode
from urllib.request import urlopen

import requests
from django.core.files.base import ContentFile
from django.utils import timezone
from social_core.exceptions import AuthForbidden

from authapp.models import ShopUserProfile, ShopUser
from geekshop.settings import MEDIA_URL, USERS_AVATARS


def save_user_profile(backend, user, response, *args, **kwargs):
    print(response)
    if backend.name == "google-oauth2":
        if 'gender' in response.keys():
            if response['gender'] == 'male':
                user.shopuserprofile.gender = ShopUserProfile.MALE
            else:
                user.shopuserprofile.gender = ShopUserProfile.FEMALE

        if 'tagline' in response.keys():
            user.shopuserprofile.tagline = response['tagline']

        if 'aboutMe' in response.keys():
            user.shopuserprofile.aboutMe = response['aboutMe']

        if 'picture' in response.keys():
            # https://lh3.googleusercontent.com/a-/AOh14GhtZ2z-Qeb9wYqrYFhudmIn0aFeTwcnet8LMBmv
            url_img = response['picture']
            # img_name = f"{response['name']}_{url_img[-6:-1]}"  # Radif_8LMBm
            # r = requests.get(url_img)
            #
            # if r.status_code == requests.codes.ok:
            #     with open(f'media/users_avatars/{img_name}.jpg', "wb") as out:
            #         out.write(r.content)
            #
            # user.avatar = f'users_avatars/{img_name}.jpg'
            img_name = f"{user.username}_{hashlib.md5(url_img.encode()).hexdigest()}.jpg"
            if not user.avatar or user.avatar != f'{USERS_AVATARS}/{img_name}':
                user.avatar.save(img_name, ContentFile(urlopen(url_img).read()))

        if 'ageRange' in response.keys():
            minAge = response['ageRange']['min']
            if int(minAge) < 18:
                user.delete()
                raise AuthForbidden('social_core.backends.google.GoogleOAuth2')
        user.save()

    elif backend.name == 'vk-oauth2':
        api_url = urlunparse(
            ('https',
             'api.vk.com',
             '/method/users.get',
             None,
             urlencode(OrderedDict(fields=','.join(('bdate', 'sex', 'about')),
                                   access_token=response['access_token'],
                                   v='5.92')),
             None
             )
        )

        resp = requests.get(api_url)
        if resp.status_code != 200:
            return

        data = resp.json()['response'][0]
        if data.get('sex'):
            user.shopuserprofile.gender = \
                ShopUserProfile.MALE if data['sex'] == 2 else ShopUserProfile.FEMALE

        if data.get('about'):
            user.shopuserprofile.aboutMe = data['about']

        if data.get('bdate'):
            bdate = datetime.strptime(data['bdate'], '%d.%m.%Y').date()

            age = timezone.now().date().year - bdate.year
            if age < 18:
                user.delete()
                raise AuthForbidden('social_core.backends.vk.VKOAuth2')

        user.save()

    # return user
