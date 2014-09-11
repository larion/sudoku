#this will print a lot of False-s why???? (solve1)

for field2 in [field2 
        for region in self.regions 
        if field in region 
        for field2 in region 
        if field2 is not field]:
            print field in region
