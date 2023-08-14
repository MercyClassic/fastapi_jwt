**<h1> FastAPI JWT Authorization </h1>**
**<h2> This package provides:</h2>**
**<h3> Storing refresh token in sql database / cache </h3>**

**<h2> Requirements </h2>**
- **<h3> FastAPI </h3>**
- **<h3> Pydantic v2 </h3>**
- **<h3> PyJWT </h3>**
- **<h3> SQLAlchemy / Redis </h3>**

**<h2> Installation </h2>**
```
pip install git+https://github.com/MercyClassic/fastapi_jwt.git
```
or if you using poetry
```
poetry add git+https://github.com/MercyClassic/fastapi_jwt.git
```
**<h2> Set up </h2>**
**<h3> If you want to store refresh token in db: </h3>**
```python
from fastapi_jwt.repositories.jwt.sqldb import JWTRepository
from fastapi_jwt.services import JWTService


class OverridenJWTRepository(JWTRepository):
    model = YourRefreshTokenModel

    
jwt_service = JWTService(OverridenJWTRepository(async_session))
```
**<h3> If you want to store refresh token in cache: </h3>**
class Redis:
pass

```python
from redis.client import Redis
from fastapi_jwt.repositories.jwt.cache import JWTRepository
from fastapi_jwt.services import JWTService
    
    
redis = Redis(host='localhost', port=6379, db=0)
jwt_service = JWTService(JWTRepository(redis))
```
`router.py`
```python
from fastapi_jwt.actions import login, logout, refresh_access_token
```
```login implementation```

![img.png](docs_images/login.jpg?raw=true)

```refresh_access_token implementation```

![img.png](docs_images/refresh.jpg?raw=true)

```logout implementation```

![img.png](docs_images/logout.jpg?raw=true)

```JWTService init params```

![img.png](docs_images/jwt_service_init_params.jpg?raw=true)

**<h3> Note </h3>**
**<h4> If you choose *sqldb* storage, do not forget create RefreshToken table</h4>**
**<h4> You can override fastapi_jwt RefreshToken </h4>**
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ForeignKey
from fastapi_jwt.models import RefreshToken


class OverridenRefreshToken(RefreshToken):
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('YourUserModel.id'), nullable=False)
``` 
**<h4> You can override </h4>**
![img.png](docs_images/extra_info.jpg?raw=true)
**<h4> To pass extra info to access token </h4>**
**<h2> I'm glad you're using my jwt auth package! :) </h2>**
