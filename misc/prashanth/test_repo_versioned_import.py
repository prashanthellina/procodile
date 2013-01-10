from procodile.repository.client.utils import Repository

r = Repository('http://www.procodile.com/repo', '/media/data/code/blockworld/checkout/blockworld/misc/prashanth/repo')
c = r.get('core.city.Generator', '1.0')
