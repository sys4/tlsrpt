
TARGETS = tlsrpt-collectd.1 tlsrpt-fetcher.1 tlsrpt-reportd.1
TARGETS += tlsrpt_add_delivery_request_failure.3 tlsrpt_add_mx_host_pattern.3 tlsrpt_add_policy_string.3 tlsrpt_cancel_delivery_request.3 tlsrpt_close.3 tlsrpt_errno_from_error_code.3 tlsrpt_error_code_is_internal.3 tlsrpt_finish_delivery_request.3 tlsrpt_finish_policy.3 tlsrpt_get_socket.3 tlsrpt_init_delivery_request.3 tlsrpt_init_policy.3 tlsrpt_open.3 tlsrpt_set_blocking.3 tlsrpt_set_malloc_and_free.3 tlsrpt_set_nonblocking.3 tlsrpt_strerror.3

.phony: all clean interim

all: ${TARGETS}

interim : ../TLSRPT-c-library-API-Documentation.adoc
	python3 ../../tools/manpage_generator/library_manpage_generator.py ../TLSRPT-c-library-API-Documentation.adoc .

${TARGETS:%.3=%.adoc} : interim

%.1 %.3 : %.adoc manpage-*.adoc Makefile
	asciidoctor -b manpage $<

clean:
	rm ${TARGETS} tlsrpt_*.adoc
