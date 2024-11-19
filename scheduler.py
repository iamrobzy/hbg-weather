import modal

app = modal.App('scheduler')

@app.function(schedule=modal.Period(seconds=10))
def update():
    print('Updating...')
