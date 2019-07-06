#include <QCoreApplication>
#include <tests.h>
#include <lib1.h>

int main(int argc, char **argv)
{
	QCoreApplication app{argc, argv};
	Lib1::lib1();

	return 0;
}
