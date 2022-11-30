import subprocess
import argparse
import consts


def get_nested_images(image_folders):
    temp = []
    for i in range(len(image_folders)):
        res = subprocess.run(['gcloud container images list --repository='+image_folders[i]],stdout=subprocess.PIPE,shell=True)
        result = res.stdout.decode('UTF-8').splitlines()
        if(len(result)!=0):
            # del image_folders[i] # this deletes the orignal array as well. by ref
            del result[0] # "Name"
            temp += get_nested_images(result)
        else:
            temp.append(image_folders[i])
    return temp

def get_list_tags(image):
    # if image does not exist it might throw error but with previous functions call
    # error shouldn't happen. Can secure this part next time.
    res = subprocess.run(['gcloud container images list-tags '+image],stdout=subprocess.PIPE,shell=True)
    result = res.stdout.decode('UTF-8').splitlines()
    del result[0]
    tags = [item.split()[1] for item in result]
    temp=[]
    for tag in tags: # split up images with multiple tag
        if ',' in tag:
            l = tag.split(',')
            l.reverse()
            temp+=l
        else:
            temp.append(tag)
    temp.reverse() # reverse chronogical order when upload
    return temp

def migrate(fr,to,tag):
    print(f'gcloud container images add-tag {fr}:{tag} {to}:{tag}')
    res = subprocess.run([f'gcloud container images add-tag {fr}:{tag} {to}:{tag}'],stdout=subprocess.PIPE,shell=True,input='y\n'.encode('utf-8'))
    result = res.stdout.decode('UTF-8').splitlines()
    print(result)

class GCPImageMigration:
    def __init__(self,**kwargs):
        print(kwargs)
        self.original_host= kwargs.get('original_host')
        self.migrated_host= kwargs.get('migrated_host')
        self.original_project= kwargs.get('original_project')
        self.migrated_project= kwargs.get('migrated_project')
        self.images= kwargs.get('images')
        # self.tags= kwargs.get('tags')
        self.nested= kwargs.get('nested')
    
    def run(self):
        root = []
        if(self.images == None):
            root.append(f'{self.original_host}/{self.original_project}')
        if(self.nested):
             root += self.images
             self.images = get_nested_images(root)
        print(f'migrating {self.images}')
        for image in self.images:
            print(f'starting migrate for {image}')
            tags = get_list_tags(image)
            print(f'tags : {tags}')
            image_name = '/'.join(image.split('/')[2:]) #skip hostname and project
            migrate_image_name = f'{self.migrated_host}/{self.migrated_project}/{image_name}'
            print(migrate_image_name)
            for tag in tags: 
                migrate(image,migrate_image_name,tag)

        return


def run():
    parser = argparse.ArgumentParser(
                    prog = 'GCP GCR Migrate',
                    description = 'Migrate GCR images into another proj')
    parser.add_argument("-oh","--original_host",default=consts.ORIGINAL_HOSTNAME)
    parser.add_argument("-mh","--migrated_host",default=consts.MIGRATED_HOSTNAME)
    parser.add_argument("-op","--original_project",default=consts.ORIGINAL_PROJECT)
    parser.add_argument("-mp","--migrated_project",default=consts.MIGRATED_PROJECT)
    parser.add_argument("-i","--images",nargs="+",default=consts.IMAGES )
    # parser.add_argument("-t","--tags",nargs="+")
    parser.add_argument("-n","--nested", action="store_true")
    
    args = parser.parse_args()
    migrate = GCPImageMigration(**vars(args))
    migrate.run()
    if(args.original_project == None or args.migrated_project == None): 
        # if migrating just host use the same proj
        print("missing projects")
        raise ValueError()
    


if __name__ == "__main__":
    run()
