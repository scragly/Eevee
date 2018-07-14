from aiocontextvars import Context

async def context_test_func(number):
    print('start context_test_func')
    if Context.current().inherited:
        print('Inherited!')
    ctx_value = _ctx_.get()
    print('ctx value is ' + str(ctx_value))
    print('setting ctx value to ' + str(number*1000))
    _ctx_.set(number*1000)
