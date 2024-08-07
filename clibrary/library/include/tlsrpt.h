/*
    Copyright (C) 2024 sys4 AG
    Author Boris Lohner bl@sys4.de

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this program.
    If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _TLSRPT_H
#define _TLSRPT_H

#ifdef  __cplusplus
extern "C" {
#endif

#include <stdlib.h>
  
#define TLSRPT_MAXDOMAINNAMELEN 256

typedef enum {
  TLSRPT_POLICY_TLSA = 1,
  TLSRPT_POLICY_STS = 2,
  TLSRPT_NO_POLICY_FOUND = 9
} tlsrpt_policy_type_t;

typedef enum {
  TLSRPT_FINAL_SUCCESS = 0,
  TLSRPT_FINAL_FAILURE = 1
} tlsrpt_final_result_t;

typedef enum {
  /* TLS negotiation failures */
  TLSRPT_STARTTLS_NOT_SUPPORTED = 201,
  TLSRPT_CERTIFICATE_HOST_MISMATCH = 202,
  TLSRPT_CERTIFICATE_NOT_TRUSTED = 203,
  TLSRPT_CERTIFICATE_EXPIRED = 204,
  TLSRPT_VALIDATION_FAILURE = 205,

  /* MTA-STS related failures */
  TLSRPT_STS_POLICY_FETCH_ERROR = 301,
  TLSRPT_STS_POLICY_INVALID = 302,
  TLSRPT_STS_WEBPKI_INVALID = 303,

  /* DNS related failures */
  TLSRPT_TLSA_INVALID = 304,
  TLSRPT_DNSSEC_INVALID = 305,
  TLSRPT_DANE_REQUIRED = 306,

  /* Internal library errors, only used within the library */
  TLSRPT_UNFINISHED_POLICY = 901

} tlsrpt_failure_t;


struct tlsrpt_connection_t;
struct tlsrpt_dr_t;

/* Handling of the connection */
int tlsrpt_open(struct tlsrpt_connection_t** pcon, const char* socketname);
int tlsrpt_close(struct tlsrpt_connection_t** pcon);

/* Handling of a single delivery request, an open connection is required */
  int tlsrpt_init_delivery_request(struct tlsrpt_dr_t** pdr, struct tlsrpt_connection_t* con, const char* domainname, const char* policyrecord);
int tlsrpt_cancel_delivery_request(struct tlsrpt_dr_t** pdr);
int tlsrpt_finish_delivery_request(struct tlsrpt_dr_t** pdr);

/* Handling of a policy within a delivery request, an initialized delivery request object is required */
int tlsrpt_init_policy(struct tlsrpt_dr_t* dr, tlsrpt_policy_type_t policy_type, const char* policydomainname);
int tlsrpt_finish_policy(struct tlsrpt_dr_t* dr, tlsrpt_final_result_t final_result);

/* Defining the policy details, an initialized delivery request object with an initialized policy is required */
int tlsrpt_add_policy_string(struct tlsrpt_dr_t* dr, const char* policy_string);
int tlsrpt_add_mx_host_pattern(struct tlsrpt_dr_t* dr, const char* mx_host_pattern);

/* Reporting a failure during a delivery request, an initialized delivery request object with an initialized policy is required */
int tlsrpt_add_delivery_request_failure(struct tlsrpt_dr_t* dr, tlsrpt_failure_t failure_code, const char* sending_mta_ip,
 const char* receiving_mx_hostname,
 const char* receiving_mx_helo,
 const char* receiving_ip,
 const char* additional_information,
 const char* failure_reason_code);

/* Extract the errno from an error code return by any of t tlsrpt library functions
*/
int tlsrpt_errno_from_error_code(int errorcode);

/* Debug and development tools */
void tlsrpt_set_blocking();
void tlsrpt_set_nonblocking();

/* Chosing a different malloc implementation */
void tlsrpt_set_malloc_and_free(void* (*malloc_function)(size_t size), void (*free_function)(void *ptr));

#ifdef __cplusplus
}
#endif

#endif /* _TLSRPT_H */
