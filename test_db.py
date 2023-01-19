from database.database import *

if __name__ == "__main__":
    temp_list = [{'name': '007', 'id': 49}, {'name': 'ruDemo', 'id': 69}, {'name': 'TeamForce', 'id': 1}]

    # drop_tables()
    # create_tables()
    #
    # user = create_user_if_not_exist(tg_id=2222438149, tg_username="third user")
    #
    # for i in temp_list:
    #     org = create_organization_if_not_exist(org_name=i['name'], id=i['id'])
    #     bind_user_org(user=user, org=org)

    # deactivate_all(tg_id=5148438149)
    #
    # activate_org(tg_id=5148438149, org_id=49)

    # print(get_all_organizations(tg_id=2222438149))

    # active_group_id = session.query(UO).filter(UO.user_id == 5148438149).filter(UO.is_active == True).first()
    # print(active_group_id.org_id)
    #
    # print(find_active_organization(5148438149))