echo 'Removing: appengine/lib'
rm -rf appengine/lib
echo 'Removing: bin'
rm -rf bin
echo 'Removing: develop-eggs'
rm -rf develop-eggs
echo 'Removing: downloads'
rm -rf downloads
echo 'Removing: eggs'
rm -rf eggs
echo 'Removing: node_modules'
rm -rf node_modules
echo 'Removing: appengine/src/greenday_public/static-dev/libs'
rm -rf appengine/src/greenday_public/static-dev/libs
echo 'Removing: parts'
rm -rf parts
echo 'Removing: reports'
rm -rf reports
echo 'Removing: target'
rm -rf target
echo 'Removing: ./.installed.cfg'
rm -rf ./.installed.cfg
echo 'Removing: ./.mr.developer.cfg'
rm -rf ./.mr.developer.cfg

echo 'Running buildout'
buildout
