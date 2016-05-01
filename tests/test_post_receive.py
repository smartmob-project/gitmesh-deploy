from gitmesh_deploy import post_receive


def test_post_receive_with_empty_dictionnary():
    post_receive({})


def test_post_receive_with_other_branch_than_master():
    post_receive({'refs/heads/branch': ('a', 'b')})


def test_post_receive_with_master():
    post_receive({'refs/heads/master': ('a', 'b')})
