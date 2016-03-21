Le plus simple:
make -f makefile.linux




Détail de tout celà:
(parmi les nombreuses sources: ) http://stackoverflow.com/questions/496664/c-dynamic-shared-library-on-linux


Sous OSX:
g++ -dynamiclib -flat_namespace tst_lib.cpp #-o tst_lib.so
g++ main.cpp -o main



Sous Linux:
g++ -fPIC -shared myclass.cc -o myclass.so
g++ class_user.cc -ldl -o class_user

Transformer des .o en .so
gcc -O3 -fPIC -c toto1.c
gcc -O3 -fPIC -c toto2.c
gcc -shared -Wl,-soname,libtoto.so.1 -o libtoto.so.1.0 toto1.o toto2.o
