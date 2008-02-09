#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "fcgiapp.h"
#define DATA_SIZE 100000

int main ()
{
	FCGX_Stream *in, *out, *err;
	FCGX_ParamArray envp;
	char *data = (char *)malloc(sizeof(char)*DATA_SIZE);
	data = memset(data, 'x', DATA_SIZE);

	while (FCGX_Accept(&in, &out, &err, &envp) >= 0) {
		
		//FCGX_PutStr("Content-Length: 12\r\n\r\nhello world\n", 34, out);
		FCGX_FPrintF(out, "Content-Length: %d\r\n\r\n", DATA_SIZE);
		FCGX_PutStr(data, DATA_SIZE, out);
		
	} /* while */
	
	free(data);
	return 0;
}
