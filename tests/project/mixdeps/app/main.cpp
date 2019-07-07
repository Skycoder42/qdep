#include <QCoreApplication>
#include <tests.h>
#include <lib1.h>
#include <lib2.h>

int main(int argc, char **argv)
{
	QCoreApplication app{argc, argv};
	Lib1::lib1();
	Lib2::lib2();

	return 0;
}
