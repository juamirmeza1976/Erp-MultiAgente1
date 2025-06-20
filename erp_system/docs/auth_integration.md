# Estrategia de Integración de Autenticación y Protección de Microservicios

Este documento describe cómo los microservicios dentro del sistema ERP validarán los tokens JWT emitidos por el `Auth Service` para proteger sus endpoints.

## 1. Visión General

El `Auth Service` es responsable de autenticar a los usuarios y emitir JSON Web Tokens (JWT). Otros microservicios (Servicios de Recursos, como `inventario_service`) deben validar estos tokens antes de permitir el acceso a sus recursos protegidos.

## 2. Estrategia de Validación de Tokens JWT

Para la fase inicial, se utilizará una estrategia de **validación local de tokens HS256**.

*   **Algoritmo JWT**: HS256 (HMAC con SHA-256), que es un algoritmo de clave simétrica.
*   **Clave Secreta (`SECRET_KEY`)**: La misma `SECRET_KEY` utilizada por `Auth Service` para firmar los tokens deberá estar disponible de forma segura para cada microservicio que necesite validar tokens.
    *   **Importante**: Compartir la `SECRET_KEY` es una simplificación para esta fase inicial. Introduce un riesgo de seguridad si la clave se ve comprometida en cualquier servicio. Debe gestionarse de forma segura (ej. a través de variables de entorno o un servicio de configuración seguro).

### Ventajas (Fase Inicial):
*   **Simplicidad**: Relativamente fácil de implementar.
*   **Rendimiento**: La validación local es rápida ya que no requiere llamadas de red adicionales al `Auth Service`.

### Desventajas y Consideraciones Futuras:
*   **Seguridad de la Clave**: La `SECRET_KEY` debe protegerse en cada servicio. Si un servicio se ve comprometido, la clave también lo estará, afectando a todo el sistema.
*   **Revocación de Tokens**: La validación local no permite una fácil revocación centralizada de tokens. Si un token necesita ser invalidado antes de su expiración, los servicios que validan localmente no se enterarán a menos que se implemente un mecanismo adicional (ej. listas de revocación consultadas periódicamente).
*   **Escalabilidad de la Gestión de Claves**: Si hay muchos microservicios, la distribución segura de la `SECRET_KEY` se vuelve más compleja.

### Mejoras Futuras Sugeridas:
1.  **Cambiar a Algoritmos Asimétricos (RS256)**:
    *   `Auth Service` firma los tokens con una clave privada.
    *   Los servicios de recursos validan los tokens con la clave pública correspondiente.
    *   Esto es más seguro ya que la clave privada solo reside en `Auth Service`. Los servicios de recursos solo necesitan la clave pública, que no es sensible.
2.  **Endpoint de Introspección de Tokens**:
    *   `Auth Service` expone un endpoint (ej. `/auth/token/introspect`) donde otros servicios pueden enviar un token para su validación.
    *   Centraliza la lógica de validación y permite la revocación inmediata.
    *   Introduce latencia de red.
3.  **API Gateway para Validación Centralizada**:
    *   Un API Gateway puede interceptar todas las solicitudes, validar el token (ya sea localmente con RS256 o llamando al `Auth Service`) y luego enriquecer la solicitud con información del usuario antes de reenviarla al microservicio correspondiente.

## 3. Esbozo de Implementación en `inventario_service`

Para proteger los endpoints en `inventario_service` (y otros servicios similares), se seguirán los siguientes pasos:

1.  **Configuración Segura de `SECRET_KEY`**:
    *   Añadir `SECRET_KEY`, `ALGORITHM` a las variables de entorno y al objeto de configuración (`Settings`) en `inventario_service/database.py`, asegurándose de que coincidan con los valores del `Auth Service`.

2.  **Dependencia de Autenticación en `inventario_service`**:
    *   Crear una dependencia similar a `get_current_user` del `Auth Service` dentro de `inventario_service/main.py` o un nuevo `core.py`.
    *   Esta dependencia:
        *   Utilizará `OAuth2PasswordBearer` (aunque el `tokenUrl` no será usado directamente por el servicio de recurso para *obtener* el token, sí lo es para la especificación OpenAPI).
        *   Decodificará el token JWT usando la `SECRET_KEY` y el `ALGORITHM` compartidos.
        *   Extraerá la información del usuario (ej. `username` o `user_id` del campo `sub`).
        *   Opcionalmente, podría buscar al usuario en su propia base de datos si necesita más información local o para verificar su existencia/estado (esto es menos común si se confía completamente en el `Auth Service` para la identidad).
        *   Manejará excepciones `JWTError` o de token inválido, devolviendo HTTP 401.

    ```python
    # Ejemplo conceptual para inventario_service/core.py o main.py

    from fastapi import Depends, HTTPException, status
    from fastapi.security import OAuth2PasswordBearer
    from jose import JWTError, jwt
    from pydantic import BaseModel, Field # Field alias was not used, so removed.
    from typing import Optional

    # Asumir que 'settings' se importa desde inventario_service.database
    # y contiene SECRET_KEY, ALGORITHM
    # from .database import settings

    oauth2_scheme_inventario = OAuth2PasswordBearer(tokenUrl="/auth/login") # Placeholder, el token se obtiene del Auth Service

    class TokenPayload(BaseModel):
        sub: str # username o user_id. FastAPI/Pydantic v2 Field alias not needed if key is 'sub'
        # username: str = Field(..., alias="sub") # Example if payload key is 'sub' but model field is 'username'
        # ... otros campos que Auth Service pueda incluir en el token

    async def get_current_user_from_token(token: str = Depends(oauth2_scheme_inventario)) -> TokenPayload:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            # Usar las settings del inventario_service que deben coincidir con Auth Service
            payload_dict = jwt.decode(
                token,
                settings.SECRET_KEY, # Esta es la SECRET_KEY compartida
                algorithms=[settings.ALGORITHM] # Este es el ALGORITHM compartido
            )
            # Validar que 'sub' (o el campo identificador) exista
            subject = payload_dict.get("sub")
            if subject is None:
                 raise credentials_exception
            token_data = TokenPayload(sub=subject)
        except JWTError:
            raise credentials_exception
        # Aquí no se busca el usuario en la BD de inventario, solo se valida el token.
        # Se podría añadir lógica para buscar/crear un "shadow user" si es necesario.
        return token_data
    ```

3.  **Proteger Endpoints**:
    *   Aplicar la nueva dependencia a los endpoints CRUD en `inventario_service/main.py`.
    *   Por ejemplo: `def read_all_productos(..., current_user: TokenPayload = Depends(get_current_user_from_token))`
    *   Esto asegurará que solo las solicitudes con un token JWT válido puedan acceder a estos recursos.

4.  **Actualizar Pruebas en `inventario_service`**:
    *   Las pruebas para los endpoints protegidos necesitarán obtener un token (simulando el login a `Auth Service` o usando un token de prueba generado con la misma `SECRET_KEY`) y enviarlo en la cabecera `Authorization`.

## 4. Flujo de Autenticación General

1.  El cliente (frontend/móvil) solicita al usuario sus credenciales.
2.  El cliente envía las credenciales al endpoint `/auth/login` del `Auth Service`.
3.  `Auth Service` valida las credenciales y, si son correctas, emite un JWT.
4.  El cliente almacena este JWT de forma segura.
5.  Para acceder a un endpoint protegido en `inventario_service` (u otro), el cliente incluye el JWT en la cabecera `Authorization: Bearer <token>`.
6.  `inventario_service` recibe la solicitud, extrae el token y lo valida usando la `SECRET_KEY` compartida y el `ALGORITHM`.
7.  Si el token es válido, `inventario_service` procesa la solicitud. Si no, devuelve un error 401.

Esta estrategia proporciona un nivel básico de seguridad y puede evolucionar hacia soluciones más robustas como RS256 o introspección de tokens a medida que el sistema crece.
