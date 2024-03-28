from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPBindError 

LDAP_SERVER = 'ldap://192.168.0.58:389'

def authenticate(user_dn, password):
    server = Server(LDAP_SERVER, get_info=ALL)
    # user_dn = f"cn={username},{LDAP_SEARCH_BASE}"
    try:
        with Connection(server, user=user_dn, password=password, auto_bind=True):
            return True
    except LDAPBindError as e:
        print(f'Exception captured: {e}')
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
# LDAP服务器配置

if __name__ == '__main__':
    LDAP_ADMIN_DN = 'ou=NSTC,dc=ninestar'  # 管理员DN或具有查询权限的DN
    LDAP_ADMIN_PASSWORD = 'Nstc@0326'

    # 用户输入的用户名和密码
    admin_username = 'ai-ldap'

    # 使用管理员凭证建立连接（根据实际情况，可能可以直接用普通用户DN和密码进行绑定）
    admin_dn = f'cn={admin_username},{LDAP_ADMIN_DN}'
    res = authenticate(admin_dn, LDAP_ADMIN_PASSWORD)
    if res:
        print(f'{admin_dn} is in')
    else:
        print(f'{admin_dn} failed authentication')


    username = 'liqiang' #'10761'
    password = 'Nstc0612' #'Nstc0727'
    # 构建要查找的用户DN
    #user_dn = f"cn={username},{LDAP_USER_DN}"
    #LDAP_BASE_DN = 'OU=NSTC, DC=ninestar'
    LDAP_BASE_DN = LDAP_ADMIN_DN
    user_dn = f"cn={username},{LDAP_BASE_DN}"
    # print(f'user_dn: {user_dn}')
    #connection.bind(bind_dn=user_dn, password=password)
    res = authenticate(user_dn, password)
    if res:
        print(f'{user_dn} is in')
    else:
        print(f'{user_dn} failed authentication')

