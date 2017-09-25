class Application:

    def __init__(self, name, package, img_src, update_date, category):
        self.name = app_name
        self.package = package
        self.img_src = img_src
        self.update_date = update_date
        self.is_new = False
        self.category = category

    def set_download_true(self):
        self.is_new = True

    def set_download_false(self):
        self.is_new = False

    def to_list(self):
        return [self.name, self.package, self.img_src, self.update_date,\
            self.isDownloaded, self.category]

    def __str__(self):
        return [self.name, self.package, self.img_src, self.update_date,\
            self.isDownloaded, self.category]

