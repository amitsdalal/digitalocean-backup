#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import time

import digitalocean

# actions = droplet.get_actions()
# for action in actions:
#     print(action.status)
# manager2 = digitalocean.droplet.get


def start_backup(droplet):
    #snap_name = ubu.name + "--auto-backup--" + str(datetime.date.today())
    snap_name = droplet.name + "--auto-backup--2018-04-12"
    snap = (droplet.take_snapshot(snap_name, power_off=True))
    print("powered off", droplet.name, "taking snapshot at:", datetime.datetime.now())
    snap_action = droplet.get_action(snap["action"]["id"])
    return snap_action


def snap_completed(snap_action):
    snap_outcome = snap_action.wait(update_every_seconds=3)
    if snap_outcome:
        print(snap_action, "Snapshot completed at :", datetime.datetime.now())
        return True
    else:
        print(snap_action, "Snapshot Errored Out")
        return False


def turn_it_on(droplet):
    powered_up = droplet.power_on()
    if powered_up:
        print("powered back on")
    else:
        print("Did not power back on")


def find_old_backups(manager, older_than):
    old_snapshots = []
    last_backup_to_keep = datetime.datetime.now() - datetime.timedelta(days=older_than)

    for each_snapshot in manager.get_droplet_snapshots():
        # print(each_snapshot.name, each_snapshot.created_at, each_snapshot.id)
        if "--auto-backup--" in each_snapshot.name:
            backed_on = each_snapshot.name[each_snapshot.name.find("--auto-backup--") + 15:]
            print("backed_on", backed_on)
            backed_on_date = datetime.datetime.strptime(backed_on, "%Y-%m-%d")
            if backed_on_date < last_backup_to_keep:
                old_snapshots.append(each_snapshot)

    print("OLD SNAPSHOTS", old_snapshots)
    return old_snapshots


def purge_backups(old_snapshots):
    if old_snapshots:   # list not empty
        for each_snapshot in old_snapshots:
            print("Deleting old snapshot:", each_snapshot)
            destroyed = each_snapshot.destroy()
            if destroyed:
                print("successfully destroyed the snapshot")
            else:
                print("Error destroying the snapshot", each_snapshot)
    else:
        print("No snapshot is old enough to delete")


def tag_droplet(do_token, droplet_id):
    tag = digitalocean.Tag(token=do_token, name="--auto-backup--")
    tag.create()  # create tag if not already created
    tag.add_droplets([droplet_id])


def list_droplets(manager):
    my_droplets = manager.get_all_droplets()
    print("Listing all droplets.")
    for droplet in my_droplets:
        print(droplet, "\n")


def get_tagged(manager, tag_name):
    tagged_droplets = manager.get_all_droplets(tag_name=tag_name)
    return tagged_droplets


def list_snapshots(manager):
    all_snaps = manager.get_all_snapshots()
    print("All available snapshots are : <snapshot-id>   <snapshot-name>\n")
    for snap in all_snaps:
        print(snap)


def set_manager(do_token):
    manager = digitalocean.Manager(token=do_token)
    return manager


def get_token():
    __basefilepath__ = os.path.dirname(os.path.abspath(__file__)) + "/"
    print("base", __basefilepath__)
    with open(__basefilepath__ + '.token') as do_token_file:
        do_token = json.load(do_token_file)
        print("token", do_token["token0"])
    return do_token["token0"]


def main(list_all, list_snaps, list_tagged, list_tags, tag, delete_older_than, backup, backup_all):
    do_token = get_token()
    manager = set_manager(do_token)
    # ubu = manager.get_droplet(92043470)

    # snap_action = start_backup(ubu)
    # snap_done = snap_completed(snap_action)
    # turn_it_on(ubu)
    # print("All available tags are :", manager.get_all_tags())

    if list_all:
        list_droplets(manager)
    if list_snaps:
        list_snapshots(manager)
    if list_tagged:
        tagged_droplets = get_tagged(manager, tag_name="--auto-backup--")
        print("Listing all the tagged droplets :\n", tagged_droplets)
    if list_tags:
        print("All available tags are :", manager.get_all_tags())
    if tag:
        tag_droplet(tag)
        tagged_droplets = get_tagged(manager, tag_name="--auto-backup--")
        print("Now, the tagged droplets are:\n", tagged_droplets)
    if delete_older_than:
        old_backups = find_old_backups(manager, delete_older_than)
        purge_backups(old_backups)
    if backup:
        droplet = manager.get_droplet(backup)
        snap_action = start_backup(droplet)
        snap_done = snap_completed(snap_action)
        turn_it_on(droplet)
        if not snap_done:
            print("ERROR: SNAPSHOT FAILED")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automated offline snapshots of digitalocean droplets')
    parser.add_argument('--list-all', dest='list_all',
                        help='List all droplets', action='store_true')
    parser.add_argument('--list-snaps', dest='list_snaps',
                        help='List all snapshots', action='store_true')
    parser.add_argument('--list-tagged', dest='list_tagged',
                        help='List droplets with "--auto-backup--" tag, these will be backedup', action='store_true')
    parser.add_argument('--list-tags', dest='list_tags',
                        help='List all used tags', action='store_true')
    parser.add_argument('--tag', dest='tag', type=str,
                        help='Add tag "--auto-backup--" to the provided droplet id')
    parser.add_argument('--delete-older-than', dest='delete_older_than',
                        type=int, help='Delete backups older than')
    parser.add_argument('--backup', dest='backup', type=str,
                        help='Shutdown Backup Then Restart the given droplet')
    parser.add_argument('--backup-all', dest='backup_all',
                        help='Shutdown Backup Then Restart all tagged droplets')

    args = parser.parse_args()

    main(args.list_all, args.list_snaps, args.list_tagged, args.list_tags,
         args.tag, args.delete_older_than, args.backup, args.backup_all)
